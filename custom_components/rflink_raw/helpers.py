"""RFLink command helpers."""
from __future__ import annotations
import asyncio, logging, re, shutil
from datetime import datetime
from pathlib import Path
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN, DATA_DEBUG_RF, DATA_DEBUG_QRF, DATA_LAST_COMMAND, DATA_LAST_ERROR, DATA_LAST_RESULT, DATA_LAST_UPDATED
_LOGGER = logging.getLogger(__name__)


RF_DEBUG_LOGGERS = (
    "homeassistant.components.rflink",
    "homeassistant.components.rflink.__init__",
    "rflink",
)


def _set_rflink_logger_level(hass: HomeAssistant, enabled: bool) -> None:
    """Enable/restore Home Assistant RFLink Python logger levels.

    This intentionally does NOT send rfdebug/qrfdebug commands to the RFLink gateway.
    """
    data = hass.data.setdefault(DOMAIN, {})
    saved = data.setdefault("_rflink_raw_tools_logger_levels", {})

    if enabled:
        for logger_name in RF_DEBUG_LOGGERS:
            logger = logging.getLogger(logger_name)
            if logger_name not in saved:
                saved[logger_name] = logger.level
            logger.setLevel(logging.DEBUG)
        return

    for logger_name, level in list(saved.items()):
        logging.getLogger(logger_name).setLevel(level if isinstance(level, int) else logging.NOTSET)
    saved.clear()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")

def _is_unknown(value: object) -> bool:
    return str(value or "").strip() in {"Unknown command.", "Unknown command"}

def _friendly(value: object) -> str:
    text = str(value or "").strip()
    if _is_unknown(text):
        return "RFLink rejected that command. Use a real learned RFLink device id and on/off action."
    if text in {"'id'", '"id"', "id", "KeyError('id')", 'KeyError("id")'} or ("KeyError" in text and "id" in text):
        return (
            "RFLink could not build an outgoing command for that device id/action. "
            "This usually means the selected discovered entity is not a sendable RFLink device, "
            "the protocol is receive-only or sensor-like, random RF noise, or the remote is unsupported by the RFLink database."
        )
    return text

def _set_status(hass: HomeAssistant, *, result: str = "", error: str = "", command: str = "") -> None:
    data = hass.data.setdefault(DOMAIN, {})
    data[DATA_LAST_RESULT] = "" if _is_unknown(result) else (result or "")
    data[DATA_LAST_ERROR] = "" if _is_unknown(error) else (error or "")
    if command:
        data[DATA_LAST_COMMAND] = command
    data[DATA_LAST_UPDATED] = _now()

def _top_key(text: str, key: str) -> bool:
    return bool(re.search(rf"(?m)^{re.escape(key)}:\s*(?:#.*)?$", text))

def _normalize_action(action: str) -> str:
    cmd = (action or "").strip().lower()
    if cmd in {"turn_on", "on", "allon"}:
        return "on" if cmd != "allon" else "allon"
    if cmd in {"turn_off", "off", "alloff"}:
        return "off" if cmd != "alloff" else "alloff"
    if cmd in {"toggle", "up", "down", "stop"}:
        return cmd
    return cmd


def _device_id_from_rflink_parts(parts: list[str]) -> tuple[str, str]:
    """Convert 10;Protocol;ID;SWITCH;ON; into HA RFLink service format."""
    cleaned = [p.strip() for p in parts if p and p.strip()]
    if cleaned and cleaned[0] == "10":
        cleaned = cleaned[1:]
    if len(cleaned) < 2:
        raise HomeAssistantError("Command must include an RFLink device id and action.")
    action = _normalize_action(cleaned[-1])
    device_parts = cleaned[:-1]
    device_id = device_parts[0] if len(device_parts) == 1 else "_".join(device_parts)
    return device_id.lower(), action


def _parse(raw: str) -> tuple[str, str]:
    """Parse user/candidate command into HA RFLink device_id and command."""
    clean = (raw or "").strip()
    if not clean:
        raise HomeAssistantError("Paste a learned RFLink device id/action first.")
    clean = clean.rstrip(";")
    if "|" in clean:
        left, right = clean.split("|", 1)
        return left.strip(), _normalize_action(right)
    if ";" in clean:
        return _device_id_from_rflink_parts([p.strip() for p in clean.split(";") if p.strip()])
    pieces = clean.split()
    if len(pieces) >= 2:
        return pieces[0].strip(), _normalize_action(pieces[-1])
    raise HomeAssistantError("Command needs both a device id and action, for example: newkaku_0000c6c2_1;on")

def _status_kind(device_id: str, command: str) -> str | None:
    d, c = (device_id or '').strip().lower(), (command or '').strip().lower()
    if d == 'ping' and not c: return 'status'
    if d == 'version' and not c: return 'version'
    return None

async def _call_rflink(hass: HomeAssistant, device_id: str, command: str) -> None:
    payload = {'device_id': device_id}
    if command: payload['command'] = command
    await hass.services.async_call('rflink', 'send_command', payload, blocking=True)

async def async_send_protocol_command(hass: HomeAssistant, device_id: str, command: str, repeat: int = 1, delay_ms: int = 250) -> dict:
    device, cmd = (device_id or '').strip(), _normalize_action(command)
    if not device:
        raise HomeAssistantError("Device ID is required.")
    if not cmd:
        raise HomeAssistantError("Command/action is required. Use on or off.")
    if ";" in device:
        device, cmd = _parse(f"{device};{cmd}")
    kind = _status_kind(device, cmd)
    if kind == 'status':
        return await async_check_rflink_status(hass)
    if kind == 'version':
        return await async_check_version_support(hass)
    if 'rflink' not in hass.config.components:
        msg = "Home Assistant RFLink is not loaded. Use Setup to install/check RFLink, then restart Home Assistant."
        _set_status(hass, error=msg, command=f"{device};{cmd}".strip(';'))
        raise HomeAssistantError(msg)
    repeat, delay_ms = max(1, int(repeat or 1)), max(0, int(delay_ms or 0))
    sent = []
    try:
        for i in range(repeat):
            await _call_rflink(hass, device, cmd)
            sent.append({'device_id': device, 'command': cmd})
            if i < repeat - 1 and delay_ms:
                await asyncio.sleep(delay_ms / 1000)
    except Exception as err:
        msg = _friendly(err)
        _set_status(hass, error=msg, command=f"{device};{cmd}".strip(';'))
        raise HomeAssistantError(msg) from err
    _set_status(hass, result=f"Sent {repeat}x: {device} {cmd}".strip(), command=f"{device};{cmd}".strip(';'))
    return {'ok': True, 'sent': sent, 'repeat': repeat, 'delay_ms': delay_ms, 'device_id': device, 'command': cmd}

async def async_send_raw_command(hass: HomeAssistant, raw_command: str, repeat: int = 1, delay_ms: int = 250) -> dict:
    device, cmd = _parse(raw_command)
    result = await async_send_protocol_command(hass, device, cmd, repeat, delay_ms)
    if _status_kind(device, cmd) is None:
        _set_status(hass, result=f"Sent RFLink command: {device};{cmd}", command=f"{device};{cmd}")
    return result

async def async_check_rflink_status(hass: HomeAssistant) -> dict:
    loaded = 'rflink' in hass.config.components
    configured = await hass.async_add_executor_job(_config_has_rflink, hass.config.path('configuration.yaml'))
    if loaded:
        msg = "Home Assistant RFLink is loaded. Use Send with a learned device command for hardware testing."
    elif configured:
        msg = "RFLink is configured in YAML, but Home Assistant has not loaded it yet. Restart Home Assistant."
    else:
        msg = "RFLink is not configured. Use Setup -> Install RFLink YAML."
    _set_status(hass, result=msg, command='CHECK_STATUS')
    return {'ok': bool(loaded), 'loaded': loaded, 'configured': configured, 'message': msg}

async def async_check_version_support(hass: HomeAssistant) -> dict:
    loaded = 'rflink' in hass.config.components
    msg = "RFLink is loaded. Generic gateway version is not exposed on all HA RFLink versions." if loaded else "RFLink is not loaded yet. Use Setup to configure it, then restart Home Assistant."
    _set_status(hass, result=msg, command='CHECK_VERSION')
    return {'ok': bool(loaded), 'loaded': loaded, 'message': msg}

async def async_set_debug(hass: HomeAssistant, debug_type: str, enabled: bool) -> dict:
    """Set RFLink logging state without sending invalid RFLink gateway commands."""
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

    _set_rflink_logger_level(hass, bool(enabled))

    state_word = "enabled" if enabled else "disabled"
    if enabled:
        message = (
            f"{label} {state_word}. Press one physical remote button, then open Captured "
            "and refresh. This uses Home Assistant logging. No rfdebug/qrfdebug gateway command was sent."
        )
    else:
        message = (
            f"{label} {state_word}. Home Assistant RFLink logger levels were restored. "
            "No rfdebug/qrfdebug gateway command was sent."
        )

    _set_status(hass, result=message, command=f"{kind};logger_{state_word}")
    return {
        "ok": True,
        "local_state": bool(enabled),
        "message": message,
        "logger_mode": True,
        "gateway_command_sent": False,
    }


async def async_install_rflink_yaml(hass: HomeAssistant, port: str) -> dict:
    clean_port = (port or '').strip() or '/dev/ttyUSB0'
    try:
        result = await hass.async_add_executor_job(_install_yaml, hass.config.path('configuration.yaml'), clean_port)
        _set_status(hass, result=result['message'], command='INSTALL_RFLINK')
        return result
    except Exception as err:
        msg = f"Could not install RFLink YAML: {err}"
        _set_status(hass, error=msg, command='INSTALL_RFLINK')
        raise HomeAssistantError(msg) from err
