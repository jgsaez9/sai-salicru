"""UI setup, endpoint reconfiguration and polling options."""

from __future__ import annotations

import re
from ipaddress import ip_address
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL, CONF_TIMEOUT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .client import ModbusException, SalicruClient, SalicruError
from .const import (
    CONF_MESSAGE_WAIT,
    CONF_UNIT_ID,
    DEFAULT_MESSAGE_WAIT,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_UNIT_ID,
    DOMAIN,
    NAME,
)


def normalize_host(value: str) -> str:
    """Accept an IP address or DNS hostname, not a URL or embedded port."""
    value = value.strip().lower().rstrip(".")
    try:
        return str(ip_address(value))
    except ValueError:
        if len(value) > 253 or not all(
            re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", part) for part in value.split(".")
        ):
            raise ValueError("Enter an IP address or hostname") from None
    return value


def connection_schema(data: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data.get(CONF_NAME, NAME)): vol.All(
                str, vol.Strip, vol.Length(min=1, max=100)
            ),
            vol.Required(CONF_HOST, default=data.get(CONF_HOST, "")): str,
            vol.Required(CONF_PORT, default=data.get(CONF_PORT, DEFAULT_PORT)): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
            vol.Required(CONF_UNIT_ID, default=data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=255)
            ),
        }
    )


class SalicruConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a Salicru SLC TWIN RT3 with the IQ14700 profile."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> SalicruOptionsFlow:
        return SalicruOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return await self._async_connection_step("user", user_input)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return await self._async_connection_step("reconfigure", user_input)

    async def _async_connection_step(
        self, step: str, user_input: dict[str, Any] | None
    ) -> FlowResult:
        entry = self._get_reconfigure_entry() if step == "reconfigure" else None
        errors = {}
        data = dict(user_input or (entry.data if entry else {}))
        if user_input is not None:
            try:
                data[CONF_HOST] = normalize_host(data[CONF_HOST])
            except ValueError:
                errors[CONF_HOST] = "invalid_host"
            else:
                identity = f"{data[CONF_HOST]}:{data[CONF_PORT]}:{data[CONF_UNIT_ID]}"
                if any(
                    existing.unique_id == identity
                    and (entry is None or existing.entry_id != entry.entry_id)
                    for existing in self._async_current_entries()
                ):
                    return self.async_abort(reason="already_configured")
                options = entry.options if entry else {}
                client = SalicruClient(
                    data[CONF_HOST],
                    data[CONF_PORT],
                    data[CONF_UNIT_ID],
                    options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                    options.get(CONF_MESSAGE_WAIT, DEFAULT_MESSAGE_WAIT),
                )
                try:
                    values = await client.async_read()
                    if any(value is None for value in values.values()):
                        errors["base"] = "invalid_data"
                except ModbusException:
                    errors["base"] = "modbus_error"
                except SalicruError:
                    errors["base"] = "cannot_connect"
                if not errors:
                    if entry is not None:
                        self.hass.config_entries.async_update_entry(
                            entry, unique_id=identity, title=data[CONF_NAME], data=data
                        )
                        # Loaded entries reload through their update listener. Avoid
                        # scheduling a second reload during reconfiguration.
                        if not entry.update_listeners:
                            self.hass.config_entries.async_schedule_reload(entry.entry_id)
                        return self.async_abort(reason="reconfigure_successful")
                    await self.async_set_unique_id(identity)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=data[CONF_NAME], data=data)
        return self.async_show_form(
            step_id=step, data_schema=connection_schema(data), errors=errors
        )


class SalicruOptionsFlow(config_entries.OptionsFlow):
    """Adjust polling from the integration settings."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
                    vol.Required(
                        CONF_TIMEOUT, default=options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=30)),
                    vol.Required(
                        CONF_MESSAGE_WAIT,
                        default=options.get(CONF_MESSAGE_WAIT, DEFAULT_MESSAGE_WAIT),
                    ): vol.All(vol.Coerce(int), vol.Range(min=200, max=2000)),
                }
            ),
        )
