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


def _get_rflink_command_class():
    """Return Home Assistant's internal RFLink command bridge."""
    try:
        from homeassistant.components.rflink.entity import RflinkCommand
    except Exception as err:  # pragma: no cover - depends on HA runtime
        raise HomeAssistantError(
            "Home Assistant RFLink integration is not loaded or command bridge is unavailable."
        ) from err
    return RflinkCommand


def _parse_raw_command(raw_command: str) -> tuple[str, str]:
    """Parse a full RFLink raw command into device_id/action for the RFLink bridge.

    Examples:
      10;NewKaku;01a2b3;1;ON; -> device_id='NewKaku;01a2b3;1', action='ON'
      10;rfdebug;on;          -> device_id='rfdebug', action='on'
      10;PING;                -> device_id='PING', action=''
    """
    clean = (raw_command or "").strip()
    if not clean:
        raise HomeAssistantError("Raw command cannot be empty.")

    clean = clean.strip()
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


async def async_send_protocol_command(
    hass: HomeAssistant,
    device_id: str,
    command: str,
    repeat: int = 1,
    delay_ms: int = 250,
) -> dict:
    """Send an RFLink protocol command through Home Assistant's RFLink bridge."""
    clean_device = (device_id or "").strip()
    clean_command = (command or "").strip()
    if not clean_device:
        raise HomeAssistantError("Device ID is required.")
    if clean_command is None:
        clean_command = ""

    repeat = max(1, int(repeat or 1))
    delay_ms = max(0, int(delay_ms or 0))

    RflinkCommand = _get_rflink_command_class()
    if not RflinkCommand.is_connected():
        raise HomeAssistantError("RFLink is not connected in Home Assistant.")

    sent = []
    for index in range(repeat):
        ok = await RflinkCommand.send_command(clean_device, clean_command)
        if not ok:
            raise HomeAssistantError(f"RFLink did not acknowledge command: {clean_device} {clean_command}")
        sent.append({"device_id": clean_device, "command": clean_command})
        if index < repeat - 1 and delay_ms:
            await asyncio.sleep(delay_ms / 1000)

    result = {
        "ok": True,
        "sent": sent,
        "repeat": repeat,
        "delay_ms": delay_ms,
    }
    _set_status(
        hass,
        result=f"Sent {repeat}x: {clean_device} {clean_command}".strip(),
        command=f"{clean_device};{clean_command}",
    )
    _LOGGER.info("RFLink Raw Tools sent protocol command: %s", result)
    return result


async def async_send_raw_command(
    hass: HomeAssistant,
    raw_command: str,
    repeat: int = 1,
    delay_ms: int = 250,
) -> dict:
    """Send a raw-ish RFLink command string via the RFLink command bridge."""
    device_id, command = _parse_raw_command(raw_command)
    try:
        result = await async_send_protocol_command(hass, device_id, command, repeat, delay_ms)
        _set_status(hass, result=f"Sent raw: {raw_command}", command=raw_command)
        return result
    except Exception as err:
        _set_status(hass, error=str(err), command=raw_command)
        raise


async def async_set_debug(hass: HomeAssistant, debug_type: str, enabled: bool) -> dict:
    """Set RFDEBUG or QRFDEBUG."""
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
