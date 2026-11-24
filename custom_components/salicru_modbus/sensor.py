"""Electrical measurements, operating mode and optional raw diagnostics."""

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SalicruConfigEntry
from .const import MODES
from .entity import SalicruEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class SalicruSensorDescription(SensorEntityDescription):
    """Register and divisor for a sensor."""

    address: int
    divisor: int = 1


SENSORS = (
    SalicruSensorDescription(
        key="input_voltage",
        address=33,
        divisor=10,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SalicruSensorDescription(
        key="output_voltage",
        address=59,
        divisor=10,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SalicruSensorDescription(
        key="input_frequency",
        address=29,
        divisor=10,
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SalicruSensorDescription(
        key="output_frequency",
        address=43,
        divisor=10,
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SalicruSensorDescription(
        key="output_current",
        address=41,
        divisor=10,
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SalicruSensorDescription(
        key="load",
        address=63,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    SalicruSensorDescription(
        key="battery_level",
        address=64,
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    SalicruSensorDescription(
        key="battery_voltage",
        address=68,
        divisor=10,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SalicruSensorDescription(
        key="nominal_battery_voltage",
        address=61,
        divisor=10,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
    ),
    SalicruSensorDescription(
        key="bypass_voltage",
        address=38,
        divisor=10,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SalicruSensorDescription(
        key="bypass_frequency",
        address=34,
        divisor=10,
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SalicruSensorDescription(
        key="active_output_power",
        address=39,
        native_unit_of_measurement="W",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SalicruSensorDescription(
        key="apparent_output_power",
        address=40,
        native_unit_of_measurement="VA",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SalicruSensorDescription(
        key="nominal_active_power",
        address=26,
        divisor=100,
        native_unit_of_measurement="W",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SalicruSensorDescription(
        key="nominal_apparent_power",
        address=27,
        divisor=100,
        native_unit_of_measurement="VA",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SalicruSensorDescription(
        key="internal_temperature",
        address=67,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SalicruSensorDescription(
        key="external_battery_branches",
        address=76,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SalicruSensorDescription(
        key="power_factor",
        address=103,
        divisor=100,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SalicruSensorDescription(
        key="firmware_version",
        address=565,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SalicruSensorDescription(
        key="battery_test_result",
        address=17,
        device_class=SensorDeviceClass.ENUM,
        options=["passed", "reserved", "failed", "aborted", "in_progress", "not_started"],
    ),
    SalicruSensorDescription(
        key="charger_mode",
        address=25,
        device_class=SensorDeviceClass.ENUM,
        options=["unknown", "charging", "discharging", "float", "resting", "off"],
    ),
    SalicruSensorDescription(
        key="converter_type",
        address=28,
        device_class=SensorDeviceClass.ENUM,
        options=["unknown", "line_interactive", "online", "online_parallel"],
    ),
    SalicruSensorDescription(
        key="phase_configuration",
        address=60,
        device_class=SensorDeviceClass.ENUM,
        options=["unknown", "single_single", "two_two", "three_single", "three_three"],
    ),
    SalicruSensorDescription(
        key="operating_mode",
        address=62,
        device_class=SensorDeviceClass.ENUM,
        options=[*MODES.values(), "unknown_mode"],
    ),
    *(
        SalicruSensorDescription(
            key=key,
            address=address,
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
        )
        for key, address in (
            ("mode_code", 62), ("status_1", 1), ("status_2", 2),
            ("status_3", 3), ("status_4", 4), ("status_5", 5),
            ("status_6", 6), ("status_7", 7), ("status_8", 8),
        )
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SalicruConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(SalicruSensor(entry, description) for description in SENSORS)


class SalicruSensor(SalicruEntity, SensorEntity):
    """A numeric register or translated mode."""

    entity_description: SalicruSensorDescription

    def __init__(self, entry: SalicruConfigEntry, description: SalicruSensorDescription) -> None:
        super().__init__(entry, description.key, description.address)
        self.entity_description = description

    @property
    def native_value(self) -> int | float | str | None:
        raw = self.coordinator.data.get(self.address)
        if raw is None:
            return None
        if self.entity_description.key == "operating_mode":
            return MODES.get(raw, "unknown_mode")
        enum_maps = {
            "battery_test_result": {
                1: "passed", 2: "reserved", 3: "failed", 4: "aborted",
                5: "in_progress", 6: "not_started",
            },
            "charger_mode": {
                1: "charging", 2: "discharging", 3: "float", 4: "resting", 5: "off",
            },
            "converter_type": {1: "line_interactive", 2: "online", 3: "online_parallel"},
            "phase_configuration": {
                1: "single_single", 2: "two_two", 3: "three_single", 4: "three_three",
            },
        }
        if self.entity_description.key in enum_maps:
            return enum_maps[self.entity_description.key].get(raw, "unknown")
        if self.entity_description.key == "internal_temperature":
            return round(raw - 273.15, 1) if raw >= 273 else None
        if self.entity_description.key == "firmware_version":
            words = [self.coordinator.data.get(address) for address in range(565, 571)]
            if any(word is None for word in words):
                return None
            firmware = b"".join(word.to_bytes(2, "big") for word in words)
            return firmware.decode("ascii", errors="replace").rstrip("\x00 ")
        if self.entity_description.divisor == 1:
            return raw
        return raw / self.entity_description.divisor

    @property
    def extra_state_attributes(self) -> dict[str, int | None] | None:
        if self.entity_description.key == "operating_mode":
            return {"raw_code": self.coordinator.data.get(62)}
        return None
