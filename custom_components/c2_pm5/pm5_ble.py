from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import timedelta
from typing import Callable

from bleak.backends.device import BLEDevice
from bleak_retry_connector import (
    establish_connection,
    BleakClientWithServiceCache,
    BleakOutOfConnectionSlotsError,
    BleakNotFoundError,
    BleakConnectionError,
)

from homeassistant.core import HomeAssistant, CALLBACK_TYPE, callback
from homeassistant.components import bluetooth
from homeassistant.util import dt as dt_util

from .const import (
    BASE_UUID_FMT,
    CHAR_0031,
    CHAR_0032,
    CHAR_0033,
    CHAR_0039,
    CHAR_003A,
    CHAR_CSAFE_RX,
    CHAR_CSAFE_TX,
    CSAFE_COMMAND_WRAPPER,
    CSAFE_EXT_START,
    CSAFE_PM_SET_DATETIME,
    CSAFE_STD_START,
    CSAFE_STOP,
    CSAFE_STUFF,
    DATETIME_SYNC_CONNECT_GRACE_SECONDS,
    DATETIME_SYNC_RATE_LIMIT_SECONDS,
    DATETIME_SYNC_TIMEOUT_SECONDS,
    DEVICE_STALE_SECONDS,
    ERG_MACHINE_TYPE,
    GET_DATETIME_CONTENTS,
    IDLE_DISCONNECT_COOLDOWN_SECONDS,
    IDLE_DISCONNECT_SECONDS,
    INTERVAL_TYPE,
    ROWING_STATE,
    STROKE_STATE,
    TERMINATE_GRACE_SECONDS,
    TERMINATE_RATE_LIMIT_SECONDS,
    TERMINATE_WORKOUT_CONTENTS,
    WORKOUT_STATE,
    WORKOUT_TYPE,
)

_LOGGER = logging.getLogger(__name__)

# https://www.concept2.com/support/software-development
# https://cms.concept2.com/sites/default/files/2024-05/PM5_CSAFECommunicationDefinition_0.pdf
# https://www.concept2.sg/files/pdf/us/monitors/PM5_CSAFECommunicationDefinition.pdf


def c2_uuid(short: int) -> str:
    return BASE_UUID_FMT.format(short=short)


def u16_le(b: bytes, off: int) -> int:
    return b[off] | (b[off + 1] << 8)


def u24_le(b: bytes, off: int) -> int:
    return b[off] | (b[off + 1] << 8) | (b[off + 2] << 16)


def csafe_xor_checksum(frame_contents: bytes) -> int:
    """CSAFE checksum is byte-by-byte XOR of *frame contents* (not including start/stop flags)."""
    c = 0
    for byte in frame_contents:
        c ^= byte
    return c


def csafe_byte_stuff(payload: bytes) -> bytes:
    """
    Byte-stuff unique flag values within the stream as:
      F0 -> F3 00
      F1 -> F3 01
      F2 -> F3 02
      F3 -> F3 03
    """
    out = bytearray()
    for b in payload:
        if b == CSAFE_EXT_START:
            out += bytes([CSAFE_STUFF, 0x00])
        elif b == CSAFE_STD_START:
            out += bytes([CSAFE_STUFF, 0x01])
        elif b == CSAFE_STOP:
            out += bytes([CSAFE_STUFF, 0x02])
        elif b == CSAFE_STUFF:
            out += bytes([CSAFE_STUFF, 0x03])
        else:
            out.append(b)
    return bytes(out)


def build_csafe_standard_frame(frame_contents: bytes) -> bytes:
    """
    Build a CSAFE *standard* frame:
      F1 + stuff(contents + checksum) + F2
    """
    checksum = csafe_xor_checksum(frame_contents)
    stuffed = csafe_byte_stuff(frame_contents + bytes([checksum]))
    return bytes([CSAFE_STD_START]) + stuffed + bytes([CSAFE_STOP])


@dataclass
class PM5Data:
    values: dict


class PM5Unavailable(Exception):
    """PM5 not found / not advertising."""


class PM5BleSession:
    """Handles BLE scanning, availability, connect/reconnect, notifications, and CSAFE control."""

    def __init__(
        self,
        hass: HomeAssistant,
        device_type: str,
        address: str,
        on_data: Callable[[PM5Data], None],
        on_available: Callable[[bool], None],
    ) -> None:
        self.hass = hass
        self.address = address.upper()
        self.on_data = on_data
        self.on_available = on_available

        self._client: BleakClientWithServiceCache | None = None
        self._stop = asyncio.Event()
        self._task: asyncio.Task | None = None

        self._uuid31 = c2_uuid(CHAR_0031)
        self._uuid32 = c2_uuid(CHAR_0032)
        self._uuid33 = c2_uuid(CHAR_0033)
        self._uuid39 = c2_uuid(CHAR_0039)
        self._uuid3a = c2_uuid(CHAR_003A)

        # CSAFE control characteristics
        self._uuid_csafe_rx = c2_uuid(CHAR_CSAFE_RX)  # write to PM
        self._uuid_csafe_tx = c2_uuid(CHAR_CSAFE_TX)  # notify from PM (optional)

        # CSAFE send guards
        self._csafe_lock = asyncio.Lock()
        self._last_terminate_attempt_monotonic: float = 0.0
        self._last_datetime_sync_monotonic: float = 0.0

        self._available: bool = False
        self._avail_task: asyncio.Task | None = None
        self._connected: bool = False
        self._idle_disconnect_monotonic: float | None = None
        self._last_active_monotonic: float | None = None
        self._last_seen_monotonic: float | None = None
        self._unsub_adv: CALLBACK_TYPE | None = None
        self._workout_state_raw: int | None = None

        # Event used to wake the connect loop immediately when rediscovered
        self._available_event = asyncio.Event()
        self._connected_event = asyncio.Event()

    # ---------- Cooldown helpers ----------
    def _in_cooldown(self) -> bool:
        if self._idle_disconnect_monotonic is None:
            return False
        return time.monotonic() < (
            self._idle_disconnect_monotonic + IDLE_DISCONNECT_COOLDOWN_SECONDS
        )

    def _cooldown_remaining(self) -> float:
        if self._idle_disconnect_monotonic is None:
            return 0.0
        return max(
            0.0,
            (self._idle_disconnect_monotonic + IDLE_DISCONNECT_COOLDOWN_SECONDS)
            - time.monotonic(),
        )

    async def start(self) -> None:
        self._stop.clear()

        self._unsub_adv = bluetooth.async_register_callback(
            self.hass,
            self._async_discovered_device,
            {"address": self.address, "connectable": True},
            bluetooth.BluetoothScanningMode.ACTIVE,
        )

        self._avail_task = asyncio.create_task(self._availability_watchdog())
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop.set()

        if self._unsub_adv:
            self._unsub_adv()
            self._unsub_adv = None

        if self._avail_task:
            self._avail_task.cancel()
            await asyncio.gather(self._avail_task, return_exceptions=True)
            self._avail_task = None

        if self._task:
            await self._task
            self._task = None

        self._set_available(False)
        self._set_connected(False)

    # ---------- Advertisement callbacks / availability ----------
    @callback
    def _async_discovered_device(
        self,
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        self._last_seen_monotonic = time.monotonic()

    def _set_available(self, available: bool) -> None:
        if self._available == available:
            return

        self._available = available
        if available:
            self._available_event.set()
        else:
            self._available_event.clear()

    def _set_connected(self, connected: bool) -> None:
        if self._connected == connected:
            return

        self._connected = connected
        if connected:
            self._connected_event.set()
        else:
            self._connected_event.clear()

        self.on_available(connected)

    async def _availability_watchdog(self) -> None:
        try:
            while not self._stop.is_set():
                await asyncio.sleep(1)

                try:
                    await self._get_ble_device()
                    discoverable = True
                except PM5Unavailable:
                    discoverable = False

                if self._last_seen_monotonic is None:
                    self._set_available(discoverable)
                    continue

                age = time.monotonic() - self._last_seen_monotonic
                self._set_available(discoverable or age <= DEVICE_STALE_SECONDS)
        except asyncio.CancelledError:
            return

    # ---------- Connection loop ----------
    async def _run(self) -> None:
        backoff = 1
        while not self._stop.is_set():
            try:
                self._set_connected(False)
                await self._connect_and_listen()
                backoff = 1

            except (
                BleakOutOfConnectionSlotsError,
                BleakNotFoundError,
                BleakConnectionError,
            ):
                pass

            except PM5Unavailable as err:
                _LOGGER.debug("%s", err)

                if self._in_cooldown():
                    _LOGGER.warning("Waiting for PM5 to shut down (%s)", self.address)
                    remaining = self._cooldown_remaining()
                    stop_task = asyncio.create_task(self._stop.wait())
                    cooldown_task = asyncio.create_task(asyncio.sleep(remaining))
                    done, pending = await asyncio.wait(
                        {stop_task, cooldown_task},
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    for t in pending:
                        t.cancel()
                    await asyncio.gather(*pending, return_exceptions=True)

                    # Remove from cache so we only try to reconnect if it continues to advertise itself
                    bluetooth.async_clear_address_from_match_history(
                        self.hass, self.address
                    )
                    self._last_seen_monotonic = None
                    self._set_available(False)

                if not self._available:
                    _LOGGER.info(
                        "Waiting for PM5 to become available (%s)", self.address
                    )
                    stop_task = asyncio.create_task(self._stop.wait())
                    avail_task = asyncio.create_task(self._available_event.wait())
                    done, pending = await asyncio.wait(
                        {stop_task, avail_task},
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    for t in pending:
                        t.cancel()
                    await asyncio.gather(*pending, return_exceptions=True)

            except Exception as err:
                _LOGGER.exception("PM5 BLE error (%s): %s", self.address, err)

            self._set_connected(False)

            if self._stop.is_set():
                break

            if self._available:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)

    async def _get_ble_device(self) -> BLEDevice:
        scanner = bluetooth.async_get_scanner(self.hass)
        dev = await scanner.find_device_by_address(self.address)
        if dev is not None:
            return dev
        raise PM5Unavailable(f"PM5 not found in scanner cache: {self.address}")

    def _workout_looks_active(self) -> bool:
        """
        Decide whether it makes sense to attempt a 'terminate workout'.
        We only try if we have a workout_state and it is not already in a terminal/terminated state.
        """
        ws = self._workout_state_raw
        if ws is None:
            return False

        if ws in (11,):
            return False

        return True

    # ---------- CSAFE ----------

    async def _send_csafe_frame(self, frame: bytes) -> None:
        """
        Write CSAFE frame to PM (0x0021).

        With ESPHome BT proxy / some BLE stacks, response=False can fail intermittently.
        Try response=False first for speed, then fallback to response=True.
        """
        if not self._client:
            raise PM5Unavailable("No BLE client")

        _LOGGER.debug("CSAFE RX (%s): %s", self.address, frame.hex())

        try:
            await self._client.write_gatt_char(
                self._uuid_csafe_rx, frame, response=False
            )
            return
        except Exception as err:
            _LOGGER.debug(
                "CSAFE write (response=False) failed; retrying response=True: %s", err
            )

        await self._client.write_gatt_char(self._uuid_csafe_rx, frame, response=True)

    def _build_set_datetime_contents(self) -> bytes:
        # Use HA's configured timezone (dt_util.now() is timezone-aware and respects HA config)
        now = dt_util.now()

        if (now.second + now.microsecond / 1e6) >= 30:
            # Round up so we're accurate witin 30 seconds
            now += timedelta(minutes=1)

        y1 = now.year >> 8
        y2 = now.year & 0xFF
        mo = now.month
        dd = now.day
        hh = int(now.strftime("%I"))
        mi = now.minute
        xm = 0 if now.strftime("%p").lower() == "am" else 1

        cmd = CSAFE_PM_SET_DATETIME
        data = bytes([hh, mi, xm, mo, dd, y1, y2])
        length = 2 + len(data)  # cmd + len(data) + data
        return bytes([CSAFE_COMMAND_WRAPPER, length, cmd, len(data)]) + data

    # ---------- Workout actions ----------
    async def _terminate_workout(self) -> bool:
        """Attempt to end the current workout via CSAFE terminate screenstate."""
        if not self._client:
            return False

        now = time.monotonic()
        if (
            now - self._last_terminate_attempt_monotonic
        ) < TERMINATE_RATE_LIMIT_SECONDS:
            return False

        if not self._workout_looks_active():
            return False

        frame = build_csafe_standard_frame(TERMINATE_WORKOUT_CONTENTS)

        async with self._csafe_lock:
            now = time.monotonic()
            if (
                now - self._last_terminate_attempt_monotonic
            ) < TERMINATE_RATE_LIMIT_SECONDS:
                return False
            if not self._workout_looks_active():
                return False

            self._last_terminate_attempt_monotonic = now
            try:
                _LOGGER.info(
                    "Attempting to terminate PM5 workout via CSAFE (%s)", self.address
                )
                await self._send_csafe_frame(frame)
                return True
            except Exception as err:
                _LOGGER.warning(
                    "Failed to send CSAFE terminate workout (%s): %s", self.address, err
                )
                return False

    # ---------- Date/time actions ----------
    async def _sync_datetime(self) -> bool:
        """Sync PM5 date/time using CSAFE_PM_SET_DATETIME (0x22)."""
        if not self._client:
            return False

        now_m = time.monotonic()
        if (
            now_m - self._last_datetime_sync_monotonic
        ) < DATETIME_SYNC_RATE_LIMIT_SECONDS:
            return False

        # Proxy stacks can be touchy immediately after connect; let notifies settle.
        if DATETIME_SYNC_CONNECT_GRACE_SECONDS > 0:
            await asyncio.sleep(DATETIME_SYNC_CONNECT_GRACE_SECONDS)

        contents = self._build_set_datetime_contents()
        frame = build_csafe_standard_frame(contents)

        async with self._csafe_lock:
            # Re-check inside lock to avoid duplicate syncs on racing tasks
            now_m = time.monotonic()
            if (
                now_m - self._last_datetime_sync_monotonic
            ) < DATETIME_SYNC_RATE_LIMIT_SECONDS:
                return False

            try:
                _LOGGER.info("Syncing PM5 date/time via CSAFE (%s)", self.address)
                await asyncio.wait_for(
                    self._send_csafe_frame(frame), timeout=DATETIME_SYNC_TIMEOUT_SECONDS
                )
                self._last_datetime_sync_monotonic = now_m
                return True
            except asyncio.TimeoutError:
                _LOGGER.warning("CSAFE date/time sync timed out (%s)", self.address)
                return False
            except Exception as err:
                _LOGGER.warning(
                    "CSAFE date/time sync failed (%s): %s", self.address, err
                )
                return False

    async def _idle_watchdog(self, idle_event: asyncio.Event) -> None:
        try:
            while not self._stop.is_set():
                await asyncio.sleep(5)

                last_active = self._last_active_monotonic
                if last_active is None:
                    continue

                idle_for = time.monotonic() - last_active
                if idle_for < IDLE_DISCONNECT_SECONDS:
                    continue

                idle_event.set()
                return
        except asyncio.CancelledError:
            return

    async def _connect_and_listen(self) -> None:
        if self._in_cooldown():
            raise PM5Unavailable(
                f"Post-disconnect cooldown active ({self._cooldown_remaining():.1f}s remaining)"
            )

        if not self._available:
            raise PM5Unavailable(f"PM5 not advertising: {self.address}")

        ble_device = await self._get_ble_device()

        disconnected = asyncio.Event()
        idle_disconnect = asyncio.Event()
        loop = asyncio.get_running_loop()

        def _disconnected_callback(_client):
            loop.call_soon_threadsafe(disconnected.set)

        self._client = await establish_connection(
            BleakClientWithServiceCache,
            ble_device,
            self.address,
            disconnected_callback=_disconnected_callback,
            max_attempts=2,
        )

        try:
            # Reset idle tracking on connect
            self._last_active_monotonic = time.monotonic()
            self._idle_disconnect_monotonic = None
            self._workout_state_raw = None

            await self._client.start_notify(self._uuid31, self._handle_0031)
            await self._client.start_notify(self._uuid32, self._handle_0032)
            await self._client.start_notify(self._uuid33, self._handle_0033)
            await self._client.start_notify(self._uuid39, self._handle_0039)
            await self._client.start_notify(self._uuid3a, self._handle_003A)

            # Optional: subscribe to CSAFE TX notifications (responses), if supported
            try:
                await self._client.start_notify(self._uuid_csafe_tx, self._handle_csafe_tx)
            except Exception as err:
                _LOGGER.debug("CSAFE TX notify not available (%s): %s", self.address, err)

            _LOGGER.info("Connected to PM5 (%s)", self.address)
            self._set_connected(True)

            try:
                await self._sync_datetime()
            except Exception:
                _LOGGER.exception(
                    "Unexpected error during PM5 datetime sync (%s)", self.address
                )

            disconnect_task = asyncio.create_task(disconnected.wait())
            idle_event_task = asyncio.create_task(idle_disconnect.wait())
            idle_task = asyncio.create_task(self._idle_watchdog(idle_disconnect))
            stop_task = asyncio.create_task(self._stop.wait())

            done, pending = await asyncio.wait(
                {disconnect_task, idle_event_task, idle_task, stop_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

            if idle_disconnect.is_set() and not self._stop.is_set():
                _LOGGER.warning(
                    "PM5 idle for %d minutes; disconnecting to allow sleep (%s)",
                    IDLE_DISCONNECT_SECONDS // 60,
                    self.address,
                )

                # Try to terminate workout first
                try:
                    await self._terminate_workout()
                except Exception:
                    _LOGGER.exception(
                        "Unexpected error during PM5 workout termination (%s)", self.address
                    )

                # Give PM a moment to emit end-of-workout summaries (0039/003A)
                if not self._stop.is_set():
                    await asyncio.sleep(TERMINATE_GRACE_SECONDS)

                self._idle_disconnect_monotonic = time.monotonic()

        finally:
            _LOGGER.info("PM5 disconnected (%s)", self.address)
            self._set_connected(False)

            client = self._client
            self._client = None  # break reference cycles ASAP

            if client is not None:
                # Best-effort notify stop
                for uuid in (
                    self._uuid31, self._uuid32, self._uuid33, self._uuid39, self._uuid3a, self._uuid_csafe_tx
                ):
                    try:
                        await client.stop_notify(uuid)
                    except Exception:
                        pass
                try:
                    await client.disconnect()
                except Exception:
                    pass

    # ---------- Notification Parsers ----------
    def _bump_seen(self) -> None:
        self._last_seen_monotonic = time.monotonic()
        self._set_available(True)

    def _handle_csafe_tx(self, _uuid: str, data: bytearray) -> None:
        """Optional CSAFE TX notifications from PM (0x0022)."""
        self._bump_seen()
        _LOGGER.debug("CSAFE TX (%s): %s", self.address, bytes(data).hex())

    # 0x0031 (11 bytes) Rowing general status
    def _handle_0031(self, _uuid: str, data: bytearray) -> None:
        self._bump_seen()

        b = bytes(data)
        if len(b) < 11:
            return

        elapsed_time_s = u24_le(b, 0) / 100.0
        distance_m = u24_le(b, 3) / 10.0
        workout_type_raw = b[6]
        interval_type_raw = b[7]
        workout_state_raw = b[8]
        rowing_state_raw = b[9]
        stroke_state_raw = b[10]

        # Track workout state for terminate gating
        self._workout_state_raw = workout_state_raw

        # Treat rowing "Active" as activity
        if rowing_state_raw == 1:
            self._last_active_monotonic = time.monotonic()

        self.on_data(
            PM5Data(
                {
                    "0031_elapsed_time_s": elapsed_time_s,
                    "0031_distance_m": distance_m,
                    "0031_workout_type": WORKOUT_TYPE.get(
                        workout_type_raw, f"Unknown ({workout_type_raw})"
                    ),
                    "0031_interval_type": INTERVAL_TYPE.get(
                        interval_type_raw, f"Unknown ({interval_type_raw})"
                    ),
                    "0031_workout_state": WORKOUT_STATE.get(
                        workout_state_raw, f"Unknown ({workout_state_raw})"
                    ),
                    "0031_rowing_state": ROWING_STATE.get(
                        rowing_state_raw, f"Unknown ({rowing_state_raw})"
                    ),
                    "0031_stroke_state": STROKE_STATE.get(
                        stroke_state_raw, f"Unknown ({stroke_state_raw})"
                    ),
                }
            )
        )

    # 0x0032 (17 bytes) Rowing additional status 1
    def _handle_0032(self, _uuid: str, data: bytearray) -> None:
        self._bump_seen()

        b = bytes(data)
        if len(b) < 17:
            return

        elapsed_time_s = u24_le(b, 0) / 100.0
        speed_m_s = u16_le(b, 3) / 1000.0
        stroke_rate_spm = b[5]
        heart_rate_bpm = None if b[6] == 255 else b[6]
        current_pace_s_per_500m = u16_le(b, 7) / 100.0
        average_pace_s_per_500m = u16_le(b, 9) / 100.0
        rest_distance_m = u16_le(b, 11)
        rest_time_s = u24_le(b, 13) / 100.0
        erg_type_raw = b[16]

        self.on_data(
            PM5Data(
                {
                    "0032_elapsed_time_s": elapsed_time_s,
                    "0032_speed_m_s": speed_m_s,
                    "0032_stroke_rate_spm": stroke_rate_spm,
                    "0032_heart_rate_bpm": heart_rate_bpm,
                    "0032_current_pace_s_per_500m": current_pace_s_per_500m,
                    "0032_average_pace_s_per_500m": average_pace_s_per_500m,
                    "0032_rest_distance_m": rest_distance_m,
                    "0032_rest_time_s": rest_time_s,
                    "0032_erg_machine_type": ERG_MACHINE_TYPE.get(
                        erg_type_raw, f"Unknown ({erg_type_raw})"
                    ),
                }
            )
        )

    # 0x0033 (20 bytes) Rowing additional status 2
    def _handle_0033(self, _uuid: str, data: bytearray) -> None:
        self._bump_seen()

        b = bytes(data)
        if len(b) < 20:
            return

        elapsed_time_s = u24_le(b, 0) / 100.0
        interval_count = b[3]
        average_power_w = u16_le(b, 4)
        total_calories = u16_le(b, 6)
        split_interval_avg_pace_s_per_500m = u16_le(b, 8) / 100.0
        split_interval_avg_power_w = u16_le(b, 10)
        split_interval_avg_calories = u16_le(b, 12)
        last_split_time_s = u24_le(b, 14) / 10.0
        last_split_distance_m = u24_le(b, 17)

        self.on_data(
            PM5Data(
                {
                    "0033_elapsed_time_s": elapsed_time_s,
                    "0033_interval_count": interval_count,
                    "0033_average_power_w": average_power_w,
                    "0033_total_calories": total_calories,
                    "0033_split_interval_avg_pace_s_per_500m": split_interval_avg_pace_s_per_500m,
                    "0033_split_interval_avg_power_w": split_interval_avg_power_w,
                    "0033_split_interval_avg_calories": split_interval_avg_calories,
                    "0033_last_split_time_s": last_split_time_s,
                    "0033_last_split_distance_m": last_split_distance_m,
                }
            )
        )

    # 0x0039 (20 bytes) End-of-workout summary
    def _handle_0039(self, _uuid: str, data: bytearray) -> None:
        self._bump_seen()

        b = bytes(data)
        if len(b) < 20:
            return

        log_date = u16_le(b, 0)
        log_time = u16_le(b, 2)
        elapsed_s = u24_le(b, 4) / 100.0
        distance_m = u24_le(b, 7) / 10.0
        avg_stroke_rate = b[10]
        ending_hr = b[11]
        avg_hr = b[12]
        min_hr = b[13]
        max_hr = b[14]
        drag_avg = b[15]
        recovery_hr = b[16]
        workout_type_raw = b[17]
        avg_pace_s_per_500m = u16_le(b, 18) / 10.0

        self.on_data(
            PM5Data(
                {
                    "0039_log_entry_date": log_date,
                    "0039_log_entry_time": log_time,
                    "0039_elapsed_time_s": elapsed_s,
                    "0039_distance_m": distance_m,
                    "0039_avg_stroke_rate_spm": avg_stroke_rate,
                    "0039_ending_heart_rate_bpm": (
                        None if ending_hr in (0, 255) else ending_hr
                    ),
                    "0039_avg_heart_rate_bpm": None if avg_hr in (0, 255) else avg_hr,
                    "0039_min_heart_rate_bpm": None if min_hr in (0, 255) else min_hr,
                    "0039_max_heart_rate_bpm": None if max_hr in (0, 255) else max_hr,
                    "0039_drag_factor_avg": drag_avg,
                    "0039_recovery_heart_rate_bpm": (
                        None if recovery_hr in (0, 255) else recovery_hr
                    ),
                    "0039_workout_type": WORKOUT_TYPE.get(
                        workout_type_raw, f"Unknown ({workout_type_raw})"
                    ),
                    "0039_avg_pace_s_per_500m": avg_pace_s_per_500m,
                }
            )
        )

    # 0x003A (19 bytes) End-of-workout additional summary
    def _handle_003A(self, _uuid: str, data: bytearray) -> None:
        self._bump_seen()

        b = bytes(data)
        if len(b) < 19:
            return

        log_date = u16_le(b, 0)
        log_time = u16_le(b, 2)
        split_interval_type_raw = b[4]
        split_interval_size = u16_le(b, 5)
        split_interval_count = b[7]
        total_calories = u16_le(b, 8)
        avg_power_w = u16_le(b, 10)
        total_rest_distance_m = u24_le(b, 12)
        interval_rest_time_s = u16_le(b, 15)
        avg_calories_per_hr = u16_le(b, 17)

        self.on_data(
            PM5Data(
                {
                    "003a_log_entry_date": log_date,
                    "003a_log_entry_time": log_time,
                    "003a_split_interval_type": INTERVAL_TYPE.get(
                        split_interval_type_raw, f"Unknown ({split_interval_type_raw})"
                    ),
                    "003a_split_interval_size": split_interval_size,
                    "003a_split_interval_count": split_interval_count,
                    "003a_total_calories": total_calories,
                    "003a_avg_power_w": avg_power_w,
                    "003a_total_rest_distance_m": total_rest_distance_m,
                    "003a_interval_rest_time_s": interval_rest_time_s,
                    "003a_avg_calories_per_hr": avg_calories_per_hr,
                }
            )
        )
