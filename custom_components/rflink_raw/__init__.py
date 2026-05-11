"""RFLink Raw Tools app-first integration."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.frontend import async_register_built_in_panel, async_remove_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import CONF_COMMAND, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    DATA_DEBUG_QRF,
    DATA_DEBUG_RF,
    DATA_LAST_COMMAND,
    DATA_LAST_ERROR,
    DATA_LAST_RESULT,
    DATA_LAST_UPDATED,
    DOMAIN,
    NAME,
    PANEL_ICON,
    PANEL_MODULE,
    PANEL_TITLE,
    PANEL_URL_PATH,
    STATIC_URL,
    VERSION,
)
from .helpers import (
    async_ping_gateway,
    async_send_protocol_command,
    async_send_raw_command,
    async_set_debug,
    async_version_gateway,
)

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

SET_DEBUG_SCHEMA = vol.Schema(
    {
        vol.Required("debug_type"): vol.In(["rfdebug", "qrfdebug"]),
        vol.Required("enabled"): cv.boolean,
    }
)


def _rflink_connected() -> bool:
    """Return whether the HA RFLink bridge reports a live protocol."""
    try:
        from homeassistant.components.rflink.entity import RflinkCommand

        return bool(RflinkCommand.is_connected())
    except Exception:
        return False


def _rflink_configured(hass: HomeAssistant) -> bool:
    """Return whether configuration.yaml appears to define RFLink."""
    try:
        config_path = Path(hass.config.path("configuration.yaml"))
        text = config_path.read_text()
    except Exception:
        return False

    return bool(re.search(r"(?m)^rflink:\s*$", text))


def _rflink_config_source(hass: HomeAssistant) -> str:
    """Return a short source label for RFLink configuration."""
    return "configuration.yaml" if _rflink_configured(hass) else ""



def _clear_status_data(hass: HomeAssistant) -> None:
    """Clear transient app status shown in the UI."""
    data = hass.data.setdefault(DOMAIN, {})
    data[DATA_LAST_RESULT] = ""
    data[DATA_LAST_ERROR] = ""
    data[DATA_LAST_COMMAND] = ""
    data[DATA_LAST_UPDATED] = ""


def _clear_stale_unknown_command(hass: HomeAssistant) -> None:
    """Clear old Unknown command errors from previous UI attempts."""
    data = hass.data.setdefault(DOMAIN, {})
    if str(data.get(DATA_LAST_ERROR, "")).strip() in {"Unknown command.", "Unknown command"}:
        data[DATA_LAST_ERROR] = ""


def _status_payload(hass: HomeAssistant) -> dict[str, Any]:
    """Return app status payload."""
    data = hass.data.setdefault(DOMAIN, {})
    configured = _rflink_configured(hass)
    loaded = "rflink" in hass.config.components
    connected = _rflink_connected()

    if connected:
        readiness = "ready"
        readiness_label = "RFLink ready"
        readiness_detail = "Home Assistant RFLink command bridge reports connected."
    elif loaded or configured:
        readiness = "configured_unconfirmed"
        readiness_label = "RFLink configured"
        readiness_detail = (
            "RFLink is configured. Use Debug -> Ping gateway to check that Home Assistant "
            "loaded the RFLink integration."
        )
    else:
        readiness = "not_configured"
        readiness_label = "RFLink config not found"
        readiness_detail = "Add the normal Home Assistant rflink: configuration first."

    return {
        "version": VERSION,
        "name": NAME,
        "rflink_configured": configured,
        "rflink_loaded": loaded,
        "rflink_config_source": _rflink_config_source(hass),
        "rflink_connected": connected,
        "readiness": readiness,
        "readiness_label": readiness_label,
        "readiness_detail": readiness_detail,
        "last_result": data.get(DATA_LAST_RESULT, ""),
        "last_error": data.get(DATA_LAST_ERROR, ""),
        "last_command": data.get(DATA_LAST_COMMAND, ""),
        "last_updated": data.get(DATA_LAST_UPDATED, ""),
        "rfdebug": bool(data.get(DATA_DEBUG_RF, False)),
        "qrfdebug": bool(data.get(DATA_DEBUG_QRF, False)),
    }


@callback
def _websocket_status(hass: HomeAssistant, connection, msg) -> None:
    """Handle frontend status requests."""
    connection.send_result(msg["id"], _status_payload(hass))


async def _async_register_panel(hass: HomeAssistant) -> None:
    """Register static app files and the sidebar panel."""
    app_dir = Path(__file__).parent / "www"

    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL, str(app_dir), False)]
    )

    async_remove_panel(hass, PANEL_URL_PATH)

    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL_PATH,
        require_admin=False,
        config={
            "_panel_custom": {
                "name": "rflink-raw-tools-panel",
                "module_url": PANEL_MODULE,
                "embed_iframe": False,
            }
        },
    )


async def _async_register_backend(hass: HomeAssistant) -> None:
    """Register services and websocket command once.

    This is called from both async_setup and async_setup_entry because some HA
    loading paths can set up config entries without the frontend having the
    websocket command available yet.
    """
    data = hass.data.setdefault(DOMAIN, {})
    if data.get("_backend_registered"):
        return

    async def send_raw(call: ServiceCall) -> None:
        await async_send_raw_command(
            hass,
            call.data["raw_command"],
            call.data["repeat"],
            call.data["delay_ms"],
        )

    async def send_protocol(call: ServiceCall) -> None:
        await async_send_protocol_command(
            hass,
            call.data[CONF_DEVICE_ID],
            call.data[CONF_COMMAND],
            call.data["repeat"],
            call.data["delay_ms"],
        )

    async def ping_gateway(call: ServiceCall) -> None:
        await async_ping_gateway(hass)

    async def version_gateway(call: ServiceCall) -> None:
        await async_version_gateway(hass)

    async def set_debug(call: ServiceCall) -> None:
        await async_set_debug(hass, call.data["debug_type"], call.data["enabled"])

    async def clear_status(call: ServiceCall) -> None:
        _clear_status_data(hass)

    _clear_stale_unknown_command(hass)

    hass.services.async_register(DOMAIN, "send_raw", send_raw, schema=SEND_RAW_SCHEMA)
    hass.services.async_register(DOMAIN, "send_protocol", send_protocol, schema=SEND_PROTOCOL_SCHEMA)
    hass.services.async_register(DOMAIN, "ping_gateway", ping_gateway)
    hass.services.async_register(DOMAIN, "version_gateway", version_gateway)
    hass.services.async_register(DOMAIN, "set_debug", set_debug, schema=SET_DEBUG_SCHEMA)
    hass.services.async_register(DOMAIN, "clear_status", clear_status)

    websocket_api.async_register_command(
        hass,
        _websocket_status,
        websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
            {vol.Required("type"): "rflink_raw/status"}
        ),
    )

    data["_backend_registered"] = True


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up RFLink Raw Tools services and websocket API."""
    await _async_register_backend(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up RFLink Raw Tools from config entry."""
    await _async_register_backend(hass)
    await _async_register_panel(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload RFLink Raw Tools."""
    async_remove_panel(hass, PANEL_URL_PATH)
    return True
