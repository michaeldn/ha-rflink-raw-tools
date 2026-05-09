"""RFLink Raw Tools integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.const import CONF_COMMAND, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .helpers import async_send_direct_command, async_send_protocol_command
from .store import async_initialize_store
from .updater import restore_last_update, update_from_github

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Any(None, vol.Schema({}))}, extra=vol.ALLOW_EXTRA)

SEND_RAW_SCHEMA = vol.Schema(
    {
        vol.Required("raw_command"): cv.string,
        vol.Optional("repeat", default=1): vol.Coerce(int),
        vol.Optional("delay_ms", default=250): vol.Coerce(int),
    }
)

SEND_PROTOCOL_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_COMMAND): cv.string,
        vol.Optional("repeat", default=1): vol.Coerce(int),
        vol.Optional("delay_ms", default=250): vol.Coerce(int),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up services."""

    async def send_raw(call: ServiceCall) -> None:
        await async_send_direct_command(hass, call.data["raw_command"], call.data["repeat"], call.data["delay_ms"])

    async def send_protocol(call: ServiceCall) -> None:
        await async_send_protocol_command(
            hass,
            call.data[CONF_DEVICE_ID],
            call.data[CONF_COMMAND],
            call.data["repeat"],
            call.data["delay_ms"],
        )

    async def do_update(call: ServiceCall) -> None:
        update_from_github(hass)

    async def do_restore(call: ServiceCall) -> None:
        restore_last_update(hass)

    hass.services.async_register(DOMAIN, "send_raw", send_raw, schema=SEND_RAW_SCHEMA)
    hass.services.async_register(DOMAIN, "send_protocol", send_protocol, schema=SEND_PROTOCOL_SCHEMA)
    hass.services.async_register(DOMAIN, "update_from_github", do_update)
    hass.services.async_register(DOMAIN, "restore_last_update", do_restore)

    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up config entry."""
    await async_initialize_store(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
