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
    return datetime.now().isoformat(timespec="seconds")


def _set_status(
    hass: HomeAssistant,
    *,
    result: str = "",
    error: str = "",
    command: str = "",
) -> None:
    data = hass.data.setdefault(DOMAIN, {})
    data[DATA_LAST_RESULT] = "" if _is_unknown_command_text(result) else (result or "")
    data[DATA_LAST_ERROR] = "" if _is_unknown_command_text(error) else (error or "")
    if command:
        data[DATA_LAST_COMMAND] = command
    data[DATA_LAST_UPDATED] = _now()


def _is_unknown_command_text(value: object) -> bool:
    return str(value or "").strip() in {"Unknown command.", "Unknown command"}


def _parse_raw_command(raw_command: str) -> tuple[str, str]:
    clean = (raw_command or "").strip()
    if not clean:
        raise HomeAssistantError("Paste a learned RFLink command first.")
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
    device = (device_id or "").strip().lower()
    action = (command or "").strip().lower()
    if device == "ping" and not action:
        return "status"
    if device == "version" and not action:
        return "version"
    return None


async def _call_rflink_send_command_service(
    hass: HomeAssistant,
    device_id: str,
    command: str,
) -> None:
    payload = {"device_id": device_id}
    if command:
        payload["command"] = command
    await hass.services.async_call("rflink", "send_command", payload, blocking=True)


async def async_send_protocol_command(
    hass: HomeAssistant,
    device_id: str,
    command: str,
    repeat: int = 1,
    delay_ms: int = 250,
) -> dict:
    clean_device = (device_id or "").strip()
    clean_command = (command or "").strip()

    if not clean_device:
        raise HomeAssistantError("Device ID is required.")

    gateway_command = _is_gateway_status_command(clean_device, clean_command)
    if gateway_command == "status":
        return await async_ping_gateway(hass)
    if gateway_command == "version":
        return await async_version_gateway(hass)

    if "rflink" not in hass.config.components:
        message = "Home Assistant RFLink is not loaded. Check configuration.yaml and restart Home Assistant."
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
        if _is_unknown_command_text(message):
            message = (
                "RFLink rejected that command. Use a real learned device command on Send, "
                "not a placeholder/example."
            )
        _set_status(hass, error=message, command=f"{clean_device};{clean_command}".strip(";"))
        raise HomeAssistantError(message) from err

    result = {"ok": True, "sent": sent, "repeat": repeat, "delay_ms": delay_ms}
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
    device_id, command = _parse_raw_command(raw_command)
    result = await async_send_protocol_command(hass, device_id, command, repeat, delay_ms)
    if _is_gateway_status_command(device_id, command) is None:
        _set_status(hass, result=f"Sent raw: {raw_command}", command=raw_command)
    return result


async def async_ping_gateway(hass: HomeAssistant) -> dict:
    loaded = "rflink" in hass.config.components
    if loaded:
        message = "Home Assistant RFLink is loaded. Use Send with a learned device command for hardware testing."
    else:
        message = "Home Assistant RFLink is not loaded yet. Check configuration.yaml and restart Home Assistant."
    _set_status(hass, result=message, command="STATUS")
    return {"ok": bool(loaded), "message": message, "loaded": loaded}


async def async_version_gateway(hass: HomeAssistant) -> dict:
    loaded = "rflink" in hass.config.components
    if loaded:
        message = "Home Assistant RFLink is loaded. Generic gateway version is not exposed on all HA RFLink versions."
    else:
        message = "Home Assistant RFLink is not loaded yet. Check configuration.yaml and restart Home Assistant."
    _set_status(hass, result=message, command="VERSION")
    return {"ok": bool(loaded), "message": message, "loaded": loaded}


async def async_set_debug(hass: HomeAssistant, debug_type: str, enabled: bool) -> dict:
    kind = (debug_type or "").strip().lower()
    if kind not in {"rfdebug", "qrfdebug"}:
        message = "Debug type must be rfdebug or qrfdebug."
        _set_status(hass, result=message, command="DEBUG")
        return {"ok": False, "local_state": False, "message": message}

    data = hass.data.setdefault(DOMAIN, {})
    if kind == "rfdebug":
        data[DATA_DEBUG_RF] = bool(enabled)
        label = "Decoded RFLink logging"
    else:
        data[DATA_DEBUG_QRF] = bool(enabled)
        label = "Raw RF capture logging"

    command = "on" if enabled else "off"

    if "rflink" not in hass.config.components:
        message = f"{label} set {command} locally. Home Assistant RFLink is not loaded, so no gateway command was sent."
        _set_status(hass, result=message, command=f"{kind};{command}")
        return {"ok": False, "local_state": bool(enabled), "message": message}

    try:
        await _call_rflink_send_command_service(hass, kind, command)
        message = f"{label} turned {command}."
        _set_status(hass, result=message, command=f"{kind};{command}")
        return {"ok": True, "local_state": bool(enabled), "message": message}
    except Exception as err:
        warning = str(err) or repr(err)
        if _is_unknown_command_text(warning):
            warning = "RFLink/HA did not accept the debug command."
        message = f"{label} set {command} locally. Gateway response: {warning}"
        _set_status(hass, result=message, command=f"{kind};{command}")
        return {"ok": False, "local_state": bool(enabled), "message": message}
