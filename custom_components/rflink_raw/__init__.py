"""RFLink Raw Tools custom integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.const import CONF_COMMAND, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_DELAY_MS,
    ATTR_MODE,
    ATTR_RAW_COMMAND,
    ATTR_REPEAT,
    DOMAIN,
    PLATFORMS,
)
from .helpers import async_send_direct_command, async_send_protocol_command

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Any(None, vol.Schema({})),
    },
    extra=vol.ALLOW_EXTRA,
)

SEND_RAW_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_RAW_COMMAND): cv.string,
        vol.Optional(ATTR_REPEAT, default=1): vol.Coerce(int),
        vol.Optional(ATTR_DELAY_MS, default=250): vol.Coerce(int),
    }
)
RFDEBUG_SCHEMA = vol.Schema({vol.Required(ATTR_MODE): vol.In(["on", "off", "ON", "OFF"])})
QRFDEBUG_SCHEMA = vol.Schema({vol.Required(ATTR_MODE): vol.In(["on", "off", "ON", "OFF"])})
SEND_PROTOCOL_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_COMMAND): cv.string,
        vol.Optional(ATTR_REPEAT, default=1): vol.Coerce(int),
        vol.Optional(ATTR_DELAY_MS, default=250): vol.Coerce(int),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up RFLink Raw Tools services."""

    async def async_send_raw(call: ServiceCall) -> None:
        await async_send_direct_command(
            hass,
            call.data[ATTR_RAW_COMMAND],
            call.data.get(ATTR_REPEAT, 1),
            call.data.get(ATTR_DELAY_MS, 250),
        )

    async def async_set_rfdebug(call: ServiceCall) -> None:
        mode = call.data[ATTR_MODE].upper()
        await async_send_direct_command(hass, f"10;RFDEBUG={mode};", 1, 250)

    async def async_set_qrfdebug(call: ServiceCall) -> None:
        mode = call.data[ATTR_MODE].upper()
        await async_send_direct_command(hass, f"10;QRFDEBUG={mode};", 1, 250)

    async def async_send_protocol(call: ServiceCall) -> None:
        device_id = call.data[CONF_DEVICE_ID]
        command = call.data[CONF_COMMAND]

        ok = await async_send_protocol_command(
            hass,
            device_id,
            command,
            call.data.get(ATTR_REPEAT, 1),
            call.data.get(ATTR_DELAY_MS, 250),
        )

        if ok is False:
            raise HomeAssistantError(
                f"RFLink command timed out or was not acknowledged: {device_id} {command}"
            )

    if not hass.services.has_service(DOMAIN, "send_raw"):
        hass.services.async_register(DOMAIN, "send_raw", async_send_raw, schema=SEND_RAW_SCHEMA)

    if not hass.services.has_service(DOMAIN, "rfdebug"):
        hass.services.async_register(DOMAIN, "rfdebug", async_set_rfdebug, schema=RFDEBUG_SCHEMA)

    if not hass.services.has_service(DOMAIN, "qrfdebug"):
        hass.services.async_register(DOMAIN, "qrfdebug", async_set_qrfdebug, schema=QRFDEBUG_SCHEMA)

    if not hass.services.has_service(DOMAIN, "send_protocol"):
        hass.services.async_register(
            DOMAIN, "send_protocol", async_send_protocol, schema=SEND_PROTOCOL_SCHEMA
        )

    _LOGGER.info("RFLink Raw Tools services registered")
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up RFLink Raw Tools from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("RFLink Raw Tools UI entities registered")
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
