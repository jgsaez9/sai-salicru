"""Downloadable diagnostics without network addresses or user-assigned names."""

from homeassistant.core import HomeAssistant

from . import SalicruConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SalicruConfigEntry
) -> dict:
    coordinator = entry.runtime_data
    return {
        "profile": "slc_twin_rt3_iq14700",
        "options": dict(entry.options),
        "last_update_success": coordinator.last_update_success,
        "last_success": coordinator.last_success.isoformat() if coordinator.last_success else None,
        "registers": {str(key): value for key, value in (coordinator.data or {}).items()},
    }
