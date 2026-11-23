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
        for key, address in (("mode_code", 62), ("status_1", 1), ("status_5", 5))
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
        if self.entity_description.divisor == 1:
            return raw
        return raw / self.entity_description.divisor

    @property
    def extra_state_attributes(self) -> dict[str, int | None] | None:
        if self.entity_description.key == "operating_mode":
            return {"raw_code": self.coordinator.data.get(62)}
        return None
