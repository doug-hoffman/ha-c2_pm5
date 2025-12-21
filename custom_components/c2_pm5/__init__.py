from __future__ import annotations

import logging
from dataclasses import dataclass, field

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, PLATFORMS, CONF_ADDRESS, CONF_DEVICE_TYPE
from .pm5_ble import PM5BleSession, PM5Data

_LOGGER = logging.getLogger(__name__)


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

        self.session = PM5BleSession(hass, device_type, address, self._handle_data, self._handle_available)

    def _handle_available(self, available: bool) -> None:
        self.state.available = available
        self.async_set_updated_data(self.state)
    
    def _handle_connection(self, connected: bool) -> None:
        if self.state.connected == connected:
            return
        self.state.connected = connected
        self.async_set_updated_data(self.state)

    def _handle_data(self, data: PM5Data) -> None:
        self.state.values.update(data.values)
        self.async_set_updated_data(self.state)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    address = entry.data[CONF_ADDRESS]
    device_type = entry.data.get(CONF_DEVICE_TYPE) or f"PM5 {address}"

    coordinator = PM5Coordinator(hass, address, device_type)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await coordinator.session.start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator: PM5Coordinator = hass.data[DOMAIN].pop(entry.entry_id)
    await coordinator.session.stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)