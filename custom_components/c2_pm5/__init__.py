from __future__ import annotations

import logging
from dataclasses import dataclass, field

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_ADDRESS,
    CONF_DEVICE_TYPE,
    DOMAIN,
    EVENT_PM5_AVAILABILITY_CHANGED,
    PLATFORMS,
)
from .pm5_ble import PM5BleSession, PM5Data

_LOGGER = logging.getLogger(__name__)

SERVICE_CONNECT_HRM = "connect_hrm"

SERVICE_SCHEMA_CONNECT_HRM = vol.Schema(
    {
        vol.Required("address"): str,
        vol.Required("manufacturer_id"): vol.Coerce(int),
        vol.Required("device_type"): str,
        vol.Required("belt_id"): vol.Coerce(int),
    }
)


@dataclass
class PM5State:
    available: bool = False
    values: dict = field(default_factory=dict)


class PM5Coordinator(DataUpdateCoordinator[PM5State]):
    def __init__(self, hass: HomeAssistant, address: str, device_type: str):
        super().__init__(hass, _LOGGER, name=device_type, update_interval=None)
        self.address = address
        self.device_type = device_type
        self.state = PM5State()
        self.async_set_updated_data(self.state)

        self.session = PM5BleSession(
            hass, device_type, address, self._handle_data, self._handle_available
        )

    def _handle_available(self, available: bool) -> None:
        if available and available is not self.state.available:
            # Clear values so we don't expose stale state
            self.state.values = {}

        if available == self.state.available:
            return

        self.state.available = available
        self.async_set_updated_data(self.state)

        # Fire HA event
        self.hass.bus.async_fire(
            EVENT_PM5_AVAILABILITY_CHANGED,
            {
                "address": self.address,
                "device_type": self.device_type,
                "available": available,
            },
        )

    def _handle_data(self, data: PM5Data) -> None:
        self.state.values.update(data.values)
        self.async_set_updated_data(self.state)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    async def _handle_connect_hrm(call: ServiceCall) -> None:
        address = call.data["address"].strip().upper()

        # Locate the matching coordinator by MAC
        for _entry_id, coordinator in hass.data[DOMAIN].items():
            if getattr(coordinator, "address", "").upper() == address:
                session = getattr(coordinator, "session", None)
                if session is None:
                    raise ValueError("Coordinator has no session")
                await session.async_set_hrbelt_info(
                    call.data["manufacturer_id"],
                    call.data["device_type"],
                    call.data["belt_id"],
                )
                return

        raise ValueError(f"No configured PM5 matches address {address}")

    hass.data.setdefault(DOMAIN, {})

    address = entry.data[CONF_ADDRESS]
    device_type = entry.data.get(CONF_DEVICE_TYPE) or f"PM5 {address}"

    coordinator = PM5Coordinator(hass, address, device_type)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    hass.services.async_register(
        DOMAIN,
        SERVICE_CONNECT_HRM,
        _handle_connect_hrm,
        schema=SERVICE_SCHEMA_CONNECT_HRM,
    )

    await coordinator.session.start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator: PM5Coordinator = hass.data[DOMAIN].pop(entry.entry_id)
    await coordinator.session.stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
