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
    """Parse a full RFLink raw command into device_id/action for HA's RFLink service.

    10;NewKaku;01a2b3;1;ON; -> device_id='NewKaku;01a2b3;1', command='ON'
    10;rfdebug;on;          -> device_id='rfdebug', command='on'
    """
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


async def _call_rflink_send_command_service(
    hass: HomeAssistant,
    device_id: str,
    command: str,
) -> None:
    """Call Home Assistant's built-in rflink.send_command service.

    Using the HA service is more stable than importing internal RFLink classes.
    """
    payload = {"device_id": device_id}
    if command:
        payload["command"] = command

    await hass.services.async_call(
        "rflink",
        "send_command",
        payload,
        blocking=True,
    )


async def async_send_protocol_command(
    hass: HomeAssistant,
    device_id: str,
    command: str,
    repeat: int = 1,
    delay_ms: int = 250,
) -> dict:
    """Send an RFLink protocol command through Home Assistant's RFLink service."""
    clean_device = (device_id or "").strip()
    clean_command = (command or "").strip()

    if not clean_device:
        raise HomeAssistantError("Device ID is required.")

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
        _set_status(hass, error=str(err), command=f"{clean_device};{clean_command}".strip(";"))
        raise

    result = {
        "ok": True,
        "sent": sent,
        "repeat": repeat,
        "delay_ms": delay_ms,
    }
    _set_status(
        hass,
        result=f"Sent {repeat}x: {clean_device} {clean_command}".strip(),
        command=f"{clean_device};{clean_command}".strip(";"),
    )
    _LOGGER.info("RFLink Raw Tools sent protocol command: %s", result)
    return result


async def async_send_raw_command(
    hass: HomeAssistant,
    raw_command: str,
    repeat: int = 1,
    delay_ms: int = 250,
) -> dict:
    """Send a raw-ish RFLink command string via HA's RFLink send_command service."""
    device_id, command = _parse_raw_command(raw_command)
    result = await async_send_protocol_command(hass, device_id, command, repeat, delay_ms)
    _set_status(hass, result=f"Sent raw: {raw_command}", command=raw_command)
    return result


async def async_ping_gateway(hass: HomeAssistant) -> dict:
    """Ping/test RFLink without requiring an RFLink protocol device id.

    Home Assistant's rflink.send_command service requires device_id, so true
    gateway-only commands can fail depending on RFLink/HA support. This app-level
    ping first verifies that the rflink integration exists, then records a clear
    status instead of failing with a cryptic KeyError such as 'id'.
    """
    if "rflink" not in hass.config.components:
        message = "Home Assistant RFLink integration is not loaded."
        _set_status(hass, error=message, command="PING")
        raise HomeAssistantError(message)

    message = "RFLink integration is loaded. For hardware response, send a learned RFLink device command."
    _set_status(hass, result=message, command="PING")
    return {"ok": True, "message": message}


async def async_version_gateway(hass: HomeAssistant) -> dict:
    """Record a version check without requiring an RFLink device id."""
    if "rflink" not in hass.config.components:
        message = "Home Assistant RFLink integration is not loaded."
        _set_status(hass, error=message, command="VERSION")
        raise HomeAssistantError(message)

    message = "RFLink integration is loaded. Gateway version query is not exposed by HA's rflink.send_command service on all versions."
    _set_status(hass, result=message, command="VERSION")
    return {"ok": True, "message": message}


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
