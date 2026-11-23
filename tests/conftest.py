"""Shared fixtures using the real Home Assistant test harness."""

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.salicru_modbus.const import DOMAIN


@pytest.fixture(autouse=True)
def enable_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def sample():
    return {
        43: 500,
        59: 2294,
        63: 14,
        64: 100,
        68: 394,
        33: 2312,
        29: 500,
        41: 6,
        62: 3,
        1: 1,
        5: 16392,
    }


@pytest.fixture
def mock_read(sample):
    with patch(
        "custom_components.salicru_modbus.client.SalicruClient.async_read",
        new_callable=AsyncMock,
        return_value=sample,
    ) as mock:
        yield mock


@pytest.fixture
def entry():
    return MockConfigEntry(
        domain=DOMAIN,
        title="Salicru SAI",
        unique_id="192.0.2.10:502:1",
        data={
            "name": "Salicru SAI",
            "host": "192.0.2.10",
            "port": 502,
            "unit_id": 1,
        },
    )
