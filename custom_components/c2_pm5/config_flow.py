from __future__ import annotations

import re
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    DOMAIN,
    CONF_ADDRESS,
    CONF_DEVICE_TYPE,
    DEVICE_TYPES,
)


_MAC_RE = re.compile(r"^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$")


def _looks_like_pm5(info: BluetoothServiceInfoBleak) -> bool:
    name = (info.name or "").lower()
    return "pm5" in name


def _normalize_mac(mac: str) -> str:
    return mac.strip().upper()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._discovered_address: str | None = None
        self._discovered_name: str | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        if not _looks_like_pm5(discovery_info):
            return self.async_abort(reason="not_supported")

        address = _normalize_mac(discovery_info.address)
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        self._discovered_address = address
        self._discovered_name = discovery_info.name or f"PM5 {address}"

        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None) -> FlowResult:
        assert self._discovered_address is not None

        if user_input is not None:
            address = self._discovered_address
            device_type = user_input[CONF_DEVICE_TYPE]

            return self.async_create_entry(
                title=f"{device_type} {self._discovered_address}",
                data={
                    CONF_ADDRESS: self._discovered_address,
                    CONF_DEVICE_TYPE: device_type,
                },
            )

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_ADDRESS, default=self._discovered_address
                ): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT, read_only=True)
                ),
                vol.Required(CONF_DEVICE_TYPE, default=DEVICE_TYPES[0]): vol.In(
                    DEVICE_TYPES
                ),
            }
        )
        return self.async_show_form(step_id="confirm", data_schema=schema)

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Manual entry: allow user to supply MAC and device type."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = _normalize_mac(user_input[CONF_ADDRESS])
            device_type = user_input[CONF_DEVICE_TYPE]

            if not _MAC_RE.match(address):
                errors[CONF_ADDRESS] = "invalid_mac"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"{device_type} {address}",
                    data={
                        CONF_ADDRESS: address,
                        CONF_DEVICE_TYPE: device_type,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): str,
                vol.Required(CONF_DEVICE_TYPE, default=DEVICE_TYPES[0]): vol.In(
                    DEVICE_TYPES
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
