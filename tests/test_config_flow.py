"""Setup, failures, duplicate endpoints, options and reconfiguration."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.data_entry_flow import FlowResultType

from custom_components.salicru_modbus.client import ModbusException, SalicruError
from custom_components.salicru_modbus.config_flow import normalize_host
from custom_components.salicru_modbus.const import DOMAIN


async def test_user_success(hass, entry, mock_read):
    with patch("custom_components.salicru_modbus.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        assert result["type"] is FlowResultType.FORM
        result = await hass.config_entries.flow.async_configure(result["flow_id"], dict(entry.data))
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == entry.data
    assert result["result"].unique_id == entry.unique_id


@pytest.mark.parametrize(
    ("error", "expected"),
    [(SalicruError("offline"), "cannot_connect"), (ModbusException(43, 2), "modbus_error")],
)
async def test_connection_error(hass, entry, mock_read, error, expected):
    mock_read.side_effect = error
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data=dict(entry.data)
    )
    assert result["errors"] == {"base": expected}


async def test_invalid_register_during_setup(hass, entry, mock_read, sample):
    mock_read.return_value = {**sample, 64: None}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data=dict(entry.data)
    )
    assert result["errors"] == {"base": "invalid_data"}


async def test_duplicate_no_network(hass, entry, mock_read):
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data=dict(entry.data)
    )
    assert result["reason"] == "already_configured"
    mock_read.assert_not_awaited()


async def test_invalid_host(hass, entry, mock_read):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data={**entry.data, "host": "https://192.0.2.10"}
    )
    assert result["errors"] == {"host": "invalid_host"}
    mock_read.assert_not_awaited()


async def test_reconfigure(hass, entry, mock_read):
    entry.add_to_hass(hass)
    original_id = entry.entry_id
    with patch.object(hass.config_entries, "async_reload", new_callable=AsyncMock) as reload:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "reconfigure", "entry_id": entry.entry_id}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**entry.data, "host": "192.0.2.20"}
        )
        await hass.async_block_till_done()
    assert result["reason"] == "reconfigure_successful"
    assert entry.unique_id == "192.0.2.20:502:1"
    assert entry.data["host"] == "192.0.2.20"
    assert entry.entry_id == original_id
    reload.assert_awaited_once_with(entry.entry_id)


async def test_options(hass, entry, mock_read):
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"scan_interval": 30, "timeout": 5, "message_wait": 300}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {"scan_interval": 30, "timeout": 5, "message_wait": 300}


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [(" UPS.Local. ", "ups.local"), ("2001:0db8::1", "2001:db8::1"), ("192.0.2.1", "192.0.2.1")],
)
def test_normalize_host(raw, normalized):
    assert normalize_host(raw) == normalized
