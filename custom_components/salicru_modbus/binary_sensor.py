"""Presence and alarm bits from two shared status registers."""

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
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
    SalicruBinaryDescription(
        key="load_segment_supported", address=69, mask=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SalicruBinaryDescription(
        key="iot_connected", address=1006, mask=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SalicruBinaryDescription(
        key="charger_fault", address=1, mask=8, device_class=BinarySensorDeviceClass.PROBLEM
    ),
    SalicruBinaryDescription(
        key="battery_end_of_runtime", address=1, mask=2048,
        device_class=BinarySensorDeviceClass.BATTERY,
    ),
    SalicruBinaryDescription(
        key="input_wiring_fault", address=2, mask=32,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="input_frequency_out_of_range", address=2, mask=512,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="input_voltage_out_of_range", address=2, mask=8192,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="bypass_frequency_out_of_range", address=3, mask=128,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="bypass_fault", address=3, mask=512, device_class=BinarySensorDeviceClass.PROBLEM
    ),
    SalicruBinaryDescription(
        key="bypass_overload", address=3, mask=1024,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="output_overload_prealarm", address=4, mask=1,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="output_short_circuit_alarm", address=4, mask=2,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="output_short_circuit", address=4, mask=1024,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="emergency_stop", address=5, mask=2,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="outlet_group_1_on", address=5, mask=4096,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SalicruBinaryDescription(
        key="inverter_current_limitation", address=5, mask=32768,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="charger_voltage_too_high", address=6, mask=4,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="charger_voltage_too_low", address=6, mask=8,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="dc_dc_fault", address=6, mask=16, device_class=BinarySensorDeviceClass.PROBLEM
    ),
    SalicruBinaryDescription(
        key="high_efficiency_frequency_out_of_range", address=6, mask=512,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="high_efficiency_voltage_out_of_range", address=7, mask=1,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="inverter_fault", address=7, mask=8, device_class=BinarySensorDeviceClass.PROBLEM
    ),
    SalicruBinaryDescription(
        key="inverter_voltage_too_high", address=7, mask=64,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="inverter_voltage_too_low", address=7, mask=128,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="dc_bus_unbalanced", address=7, mask=256,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="rectifier_fault", address=7, mask=2048,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="battery_test_passed", address=8, mask=8192,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SalicruBinaryDescription(
        key="battery_test_failed", address=8, mask=16384,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    SalicruBinaryDescription(
        key="battery_test_aborted", address=8, mask=32768,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
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
