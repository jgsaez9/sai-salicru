"""Share one polling cycle between all entities."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, CONF_TIMEOUT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .client import SalicruClient, SalicruError
from .const import (
    CONF_MESSAGE_WAIT,
    CONF_UNIT_ID,
    DEFAULT_MESSAGE_WAIT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class SalicruCoordinator(DataUpdateCoordinator[dict[int, int | None]]):
    """Fetch the complete profile and handle availability/recovery."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.client = SalicruClient(
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
            entry.data[CONF_UNIT_ID],
            entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            entry.options.get(CONF_MESSAGE_WAIT, DEFAULT_MESSAGE_WAIT),
        )
        self.last_success = None

    async def _async_update_data(self) -> dict[int, int | None]:
        try:
            data = await self.client.async_read()
        except SalicruError as err:
            raise UpdateFailed(str(err)) from err
        if all(value is None for value in data.values()):
            raise UpdateFailed("The device returned no usable register values")
        self.last_success = dt_util.utcnow()
        return data
