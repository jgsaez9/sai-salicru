"""Verify entities against Home Assistant, including loss and recovery."""

import json
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er

from custom_components.salicru_modbus.client import SalicruError
from custom_components.salicru_modbus.const import DOMAIN
from custom_components.salicru_modbus.diagnostics import async_get_config_entry_diagnostics


def entity_id(hass, entry, key, platform="sensor"):
    return er.async_get(hass).async_get_entity_id(platform, DOMAIN, f"{entry.entry_id}_{key}")


async def setup(hass, entry):
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_measurements_and_registry(hass, entry, mock_read):
    await setup(hass, entry)
    registry_entries = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert len(registry_entries) == 21
    assert sum(item.disabled_by is None for item in registry_entries) == 18
    for key, expected in {
        "input_voltage": "231.2",
        "output_voltage": "229.4",
        "input_frequency": "50.0",
        "output_frequency": "50.0",
        "output_current": "0.6",
        "battery_voltage": "39.4",
        "battery_level": "100",
        "load": "14",
        "operating_mode": "line",
    }.items():
        assert hass.states.get(entity_id(hass, entry, key)).state == expected
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_alarm_bits_independently(hass, entry, mock_read, sample):
    await setup(hass, entry)
    bits = {
        "mains_present": 16384,
        "output_powered": 8,
        "low_battery": 1,
        "overload": 32,
        "over_temperature": 64,
        "internal_fault": 16,
        "replace_battery": 256,
        "fan_fault": 4,
    }
    for active_key, mask in bits.items():
        mock_read.return_value = {**sample, 5: mask}
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()
        for key in bits:
            assert hass.states.get(entity_id(hass, entry, key, "binary_sensor")).state == (
                "on" if key == active_key else "off"
            )
    mock_read.return_value = {**sample, 1: 0}
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert (
        hass.states.get(entity_id(hass, entry, "battery_present", "binary_sensor")).state == "off"
    )


async def test_communication_loss_and_recovery(hass, entry, mock_read, sample):
    await setup(hass, entry)
    mock_read.side_effect = SalicruError("offline")
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    for item in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id):
        if item.disabled_by is None:
            assert hass.states.get(item.entity_id).state == "unavailable"
    mock_read.side_effect = None
    mock_read.return_value = {**sample, 62: 4, 5: 9}
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id(hass, entry, "operating_mode")).state == "battery"
    assert hass.states.get(entity_id(hass, entry, "low_battery", "binary_sensor")).state == "on"
    assert hass.states.get(entity_id(hass, entry, "mains_present", "binary_sensor")).state == "off"


async def test_invalid_source_not_false_alarm(hass, entry, mock_read, sample):
    await setup(hass, entry)
    mock_read.return_value = {**sample, 5: None, 64: None, 62: 9}
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert (
        hass.states.get(entity_id(hass, entry, "low_battery", "binary_sensor")).state
        == "unavailable"
    )
    assert hass.states.get(entity_id(hass, entry, "battery_level")).state == "unavailable"
    mode = hass.states.get(entity_id(hass, entry, "operating_mode"))
    assert mode.state == "unknown_mode"
    assert mode.attributes["raw_code"] == 9


async def test_setup_failure_retries(hass, entry, mock_read):
    mock_read.side_effect = SalicruError("offline")
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_diagnostics_exclude_endpoint_and_name(hass, entry, mock_read):
    await setup(hass, entry)
    data = await async_get_config_entry_diagnostics(hass, entry)
    encoded = json.dumps(data)
    assert entry.data["host"] not in encoded
    assert entry.title not in encoded
    assert entry.unique_id not in encoded
    assert data["registers"]["43"] == 500
    assert data["last_update_success"] is True


async def test_loaded_reconfigure_and_options_reload_once(hass, entry, mock_read):
    await setup(hass, entry)
    with patch.object(hass.config_entries, "async_reload", new_callable=AsyncMock) as reload:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "reconfigure", "entry_id": entry.entry_id}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**entry.data, "host": "192.0.2.20", "name": "UPS office"}
        )
        await hass.async_block_till_done()
        assert result["reason"] == "reconfigure_successful"
        reload.assert_awaited_once_with(entry.entry_id)
        assert entry.title == "UPS office"
        assert entry.unique_id == "192.0.2.20:502:1"
        reload.reset_mock()
        result = await hass.config_entries.options.async_init(entry.entry_id)
        await hass.config_entries.options.async_configure(
            result["flow_id"], {"scan_interval": 30, "timeout": 5, "message_wait": 300}
        )
        await hass.async_block_till_done()
        reload.assert_awaited_once_with(entry.entry_id)
