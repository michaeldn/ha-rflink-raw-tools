"""RFLink command helpers."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DATA_DEBUG_QRF,
    DATA_DEBUG_RF,
    DATA_LAST_COMMAND,
    DATA_LAST_ERROR,
    DATA_LAST_RESULT,
    DATA_LAST_UPDATED,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _now() -> str:
    """Return an ISO timestamp for UI status."""
    return datetime.now().isoformat(timespec="seconds")


def _set_status(
    hass: HomeAssistant,
    *,
    result: str = "",
    error: str = "",
    command: str = "",
) -> None:
    """Store app status in hass.data."""
    data = hass.data.setdefault(DOMAIN, {})
    if result:
        data[DATA_LAST_RESULT] = result
    if error:
        data[DATA_LAST_ERROR] = error
    elif result:
        data[DATA_LAST_ERROR] = ""
    if command:
        data[DATA_LAST_COMMAND] = command
    data[DATA_LAST_UPDATED] = _now()


def _parse_raw_command(raw_command: str) -> tuple[str, str]:
    """Parse a full RFLink raw command into device_id/action for HA's RFLink service."""
    clean = (raw_command or "").strip()
    if not clean:
        raise HomeAssistantError("Raw command cannot be empty.")
    if clean.endswith(";"):
        clean = clean[:-1]
    parts = [part.strip() for part in clean.split(";") if part.strip()]
    if parts and parts[0] == "10":
        parts = parts[1:]
    if not parts:
        raise HomeAssistantError("Raw command does not contain a command body.")
    if len(parts) == 1:
        return parts[0], ""
    return ";".join(parts[:-1]), parts[-1]


def _is_gateway_status_command(device_id: str, command: str) -> str | None:
    """Return ping/version command type when the raw command is an app status command."""
    device = (device_id or "").strip().lower()
    action = (command or "").strip().lower()
    if device == "ping" and not action:
        return "ping"
    if device == "version" and not action:
        return "version"
    return None


async def _call_rflink_send_command_service(hass: HomeAssistant, device_id: str, command: str) -> None:
    """Call Home Assistant's built-in rflink.send_command service."""
    payload = {"device_id": device_id}
    if command:
        payload["command"] = command
    await hass.services.async_call("rflink", "send_command", payload, blocking=True)


async def async_send_protocol_command(hass: HomeAssistant, device_id: str, command: str, repeat: int = 1, delay_ms: int = 250) -> dict:
    """Send an RFLink protocol command through Home Assistant's RFLink service."""
    clean_device = (device_id or "").strip()
    clean_command = (command or "").strip()
    if not clean_device:
        raise HomeAssistantError("Device ID is required.")
    gateway_command = _is_gateway_status_command(clean_device, clean_command)
    if gateway_command == "ping":
        return await async_ping_gateway(hass)
    if gateway_command == "version":
        return await async_version_gateway(hass)
    if "rflink" not in hass.config.components:
        message = "Home Assistant RFLink integration is not loaded. Check configuration.yaml and restart Home Assistant."
        _set_status(hass, error=message, command=f"{clean_device};{clean_command}".strip(";"))
        raise HomeAssistantError(message)
    repeat = max(1, int(repeat or 1))
    delay_ms = max(0, int(delay_ms or 0))
    sent = []
    try:
        for index in range(repeat):
            await _call_rflink_send_command_service(hass, clean_device, clean_command)
            sent.append({"device_id": clean_device, "command": clean_command})
            if index < repeat - 1 and delay_ms:
                await asyncio.sleep(delay_ms / 1000)
    except Exception as err:
        message = str(err) or repr(err)
        if message.strip() in {"Unknown command.", "Unknown command"}:
            message = "RFLink reported Unknown command. Use a learned RFLink device command on Send, or use Debug for Ping/Version."
        _set_status(hass, error=message, command=f"{clean_device};{clean_command}".strip(";"))
        raise HomeAssistantError(message) from err
    result = {"ok": True, "sent": sent, "repeat": repeat, "delay_ms": delay_ms}
    _set_status(hass, result=f"Sent {repeat}x: {clean_device} {clean_command}".strip(), command=f"{clean_device};{clean_command}".strip(";"))
    _LOGGER.info("RFLink Raw Tools sent protocol command: %s", result)
    return result


async def async_send_raw_command(hass: HomeAssistant, raw_command: str, repeat: int = 1, delay_ms: int = 250) -> dict:
    """Send a raw-ish RFLink command string via HA's RFLink send_command service."""
    device_id, command = _parse_raw_command(raw_command)
    result = await async_send_protocol_command(hass, device_id, command, repeat, delay_ms)
    if _is_gateway_status_command(device_id, command) is None:
        _set_status(hass, result=f"Sent raw: {raw_command}", command=raw_command)
    return result


async def async_ping_gateway(hass: HomeAssistant) -> dict:
    """App-level RFLink status check. This intentionally never raises."""
    loaded = "rflink" in hass.config.components
    if loaded:
        message = "RFLink integration is loaded. Use a learned device command for hardware send testing."
    else:
        message = "RFLink integration is not loaded yet. Check configuration.yaml and restart Home Assistant."
    _set_status(hass, result=message, command="PING")
    return {"ok": bool(loaded), "message": message, "loaded": loaded}


async def async_version_gateway(hass: HomeAssistant) -> dict:
    """App-level RFLink version/status check. This intentionally never raises."""
    loaded = "rflink" in hass.config.components
    if loaded:
        message = "RFLink integration is loaded. Gateway VERSION is not exposed by HA's RFLink service on all versions."
    else:
        message = "RFLink integration is not loaded yet. Check configuration.yaml and restart Home Assistant."
    _set_status(hass, result=message, command="VERSION")
    return {"ok": bool(loaded), "message": message, "loaded": loaded}


async def async_set_debug(hass: HomeAssistant, debug_type: str, enabled: bool) -> dict:
    """Set RFDEBUG or QRFDEBUG through RFLink send_command."""
    kind = (debug_type or "").strip().lower()
    if kind not in {"rfdebug", "qrfdebug"}:
        raise HomeAssistantError("debug_type must be rfdebug or qrfdebug.")
    command = "on" if enabled else "off"
    result = await async_send_protocol_command(hass, kind, command, 1, 0)
    data = hass.data.setdefault(DOMAIN, {})
    if kind == "rfdebug":
        data[DATA_DEBUG_RF] = bool(enabled)
    else:
        data[DATA_DEBUG_QRF] = bool(enabled)
    _set_status(hass, result=f"{kind.upper()} turned {command}")
    return result
