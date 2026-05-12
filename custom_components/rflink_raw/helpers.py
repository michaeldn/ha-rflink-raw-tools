"""RFLink command helpers."""
from __future__ import annotations
import asyncio, logging, re, shutil
from datetime import datetime
from pathlib import Path
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN, DATA_DEBUG_RF, DATA_DEBUG_QRF, DATA_LAST_COMMAND, DATA_LAST_ERROR, DATA_LAST_RESULT, DATA_LAST_UPDATED
_LOGGER = logging.getLogger(__name__)

def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")

def _is_unknown(value: object) -> bool:
    return str(value or "").strip() in {"Unknown command.", "Unknown command"}

def _friendly(value: object) -> str:
    text = str(value or "").strip()
    if _is_unknown(text):
        return "RFLink rejected that command. Use a real learned device command, not a placeholder/example."
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

def _parse(raw: str) -> tuple[str, str]:
    clean = (raw or "").strip().rstrip(';')
    if not clean:
        raise HomeAssistantError("Paste a learned RFLink command first.")
    parts = [p.strip() for p in clean.split(';') if p.strip()]
    if parts and parts[0] == '10':
        parts = parts[1:]
    if not parts:
        raise HomeAssistantError("Raw command does not contain a command body.")
    if len(parts) == 1:
        return parts[0], ""
    return ';'.join(parts[:-1]), parts[-1]

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
    device, cmd = (device_id or '').strip(), (command or '').strip()
    if not device: raise HomeAssistantError("Device ID is required.")
    kind = _status_kind(device, cmd)
    if kind == 'status': return await async_check_rflink_status(hass)
    if kind == 'version': return await async_check_version_support(hass)
    if 'rflink' not in hass.config.components:
        msg = "Home Assistant RFLink is not loaded. Use Setup to install/check RFLink, then restart Home Assistant."
        _set_status(hass, error=msg, command=f"{device};{cmd}".strip(';'))
        raise HomeAssistantError(msg)
    repeat, delay_ms = max(1, int(repeat or 1)), max(0, int(delay_ms or 0))
    sent=[]
    try:
        for i in range(repeat):
            await _call_rflink(hass, device, cmd)
            sent.append({'device_id': device, 'command': cmd})
            if i < repeat-1 and delay_ms:
                await asyncio.sleep(delay_ms/1000)
    except Exception as err:
        msg = _friendly(err)
        _set_status(hass, error=msg, command=f"{device};{cmd}".strip(';'))
        raise HomeAssistantError(msg) from err
    _set_status(hass, result=f"Sent {repeat}x: {device} {cmd}".strip(), command=f"{device};{cmd}".strip(';'))
    return {'ok': True, 'sent': sent, 'repeat': repeat, 'delay_ms': delay_ms}

async def async_send_raw_command(hass: HomeAssistant, raw_command: str, repeat: int = 1, delay_ms: int = 250) -> dict:
    device, cmd = _parse(raw_command)
    result = await async_send_protocol_command(hass, device, cmd, repeat, delay_ms)
    if _status_kind(device, cmd) is None:
        _set_status(hass, result=f"Sent raw: {raw_command}", command=raw_command)
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
    kind = (debug_type or '').strip().lower()
    if kind not in {'rfdebug','qrfdebug'}:
        msg = 'Debug type must be rfdebug or qrfdebug.'
        _set_status(hass, result=msg, command='DEBUG')
        return {'ok': False, 'local_state': False, 'message': msg}
    data = hass.data.setdefault(DOMAIN, {})
    label = 'Decoded RFLink logging' if kind == 'rfdebug' else 'Raw RF capture logging'
    data[DATA_DEBUG_RF if kind == 'rfdebug' else DATA_DEBUG_QRF] = bool(enabled)
    cmd = 'on' if enabled else 'off'
    if 'rflink' not in hass.config.components:
        msg = f"{label} set {cmd} locally. RFLink is not loaded, so no gateway command was sent."
        _set_status(hass, result=msg, command=f"{kind};{cmd}")
        return {'ok': False, 'local_state': bool(enabled), 'message': msg}
    try:
        await _call_rflink(hass, kind, cmd)
        msg = f"{label} turned {cmd}."
        _set_status(hass, result=msg, command=f"{kind};{cmd}")
        return {'ok': True, 'local_state': bool(enabled), 'message': msg}
    except Exception as err:
        msg = f"{label} set {cmd} locally. Gateway response: {_friendly(err)}"
        _set_status(hass, result=msg, command=f"{kind};{cmd}")
        return {'ok': False, 'local_state': bool(enabled), 'message': msg}

def _config_has_rflink(config_path: str) -> bool:
    path = Path(config_path)
    return path.exists() and _top_key(path.read_text(errors='ignore'), 'rflink')

def _install_yaml(config_path: str, port: str) -> dict:
    path = Path(config_path)
    text = path.read_text(errors='ignore') if path.exists() else ''
    if _top_key(text, 'rflink'):
        return {'changed': False, 'message': 'RFLink is already configured in configuration.yaml.'}
    backup = path.with_name(f"configuration.yaml.rflink_raw_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    if path.exists(): shutil.copy2(path, backup)
    block = (
        "\n\n# RFLink Raw Tools managed block - start\n"
        "rflink:\n"
        f"  port: {port}\n"
        "  wait_for_ack: false\n"
        "  reconnect_interval: 10\n"
        "# RFLink Raw Tools managed block - end\n"
    )
    path.write_text(text.rstrip() + block + '\n')
    return {'changed': True, 'backup': str(backup), 'message': f'RFLink YAML added with port {port}. Restart Home Assistant Core.'}

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
