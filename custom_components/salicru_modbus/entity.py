"""Shared entity identity and availability."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SalicruConfigEntry
from .const import DOMAIN
from .coordinator import SalicruCoordinator


class SalicruEntity(CoordinatorEntity[SalicruCoordinator]):
    """A stable identity that survives host/port changes."""

    _attr_has_entity_name = True

    def __init__(self, entry: SalicruConfigEntry, key: str, address: int) -> None:
        super().__init__(entry.runtime_data)
        self.address = address
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Salicru",
            model="SLC TWIN RT3 (Modbus TCP)",
        )

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get(self.address) is not None
