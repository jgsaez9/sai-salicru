"""Presence and alarm bits from two shared status registers."""

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SalicruConfigEntry
from .entity import SalicruEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class SalicruBinaryDescription(BinarySensorEntityDescription):
    """Documented register and zero-based bit mask."""

    address: int = 5
    mask: int


BINARY_SENSORS = (
    SalicruBinaryDescription(
        key="mains_present", mask=16384, device_class=BinarySensorDeviceClass.POWER
    ),
    SalicruBinaryDescription(
        key="output_powered", mask=8, device_class=BinarySensorDeviceClass.POWER
    ),
    SalicruBinaryDescription(key="battery_present", address=1, mask=1),
    SalicruBinaryDescription(
        key="low_battery", mask=1, device_class=BinarySensorDeviceClass.BATTERY
    ),
    SalicruBinaryDescription(key="overload", mask=32, device_class=BinarySensorDeviceClass.PROBLEM),
    SalicruBinaryDescription(
        key="over_temperature", mask=64, device_class=BinarySensorDeviceClass.PROBLEM
    ),
    SalicruBinaryDescription(
        key="internal_fault", mask=16, device_class=BinarySensorDeviceClass.PROBLEM
    ),
    SalicruBinaryDescription(
        key="replace_battery", mask=256, device_class=BinarySensorDeviceClass.PROBLEM
    ),
    SalicruBinaryDescription(key="fan_fault", mask=4, device_class=BinarySensorDeviceClass.PROBLEM),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SalicruConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(SalicruBinarySensor(entry, description) for description in BINARY_SENSORS)


class SalicruBinarySensor(SalicruEntity, BinarySensorEntity):
    """A bit with availability inherited from its source register."""

    entity_description: SalicruBinaryDescription

    def __init__(self, entry: SalicruConfigEntry, description: SalicruBinaryDescription) -> None:
        super().__init__(entry, description.key, description.address)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get(self.address)
        return None if raw is None else bool(raw & self.entity_description.mask)
