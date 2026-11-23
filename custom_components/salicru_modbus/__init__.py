"""Salicru SAI local Modbus TCP integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import SalicruCoordinator

PLATFORMS = (Platform.SENSOR, Platform.BINARY_SENSOR)
type SalicruConfigEntry = ConfigEntry[SalicruCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SalicruConfigEntry) -> bool:
    """Validate the first update before registering entities."""
    coordinator = SalicruCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_reload_entry(hass: HomeAssistant, entry: SalicruConfigEntry) -> None:
    """Apply options without restarting Home Assistant."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: SalicruConfigEntry) -> bool:
    """Unload entities and their coordinator subscriptions."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
