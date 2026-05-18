"""RFLink Raw Tools app-first integration."""
from __future__ import annotations
from pathlib import Path
import re
from typing import Any
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.components.frontend import async_register_built_in_panel, async_remove_panel
from homeassistant.components.http import HomeAssistantView, StaticPathConfig
from homeassistant.const import CONF_COMMAND, CONF_DEVICE_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.dispatcher import async_dispatcher_send
from .const import DOMAIN, NAME, VERSION, PANEL_ICON, PANEL_MODULE, PANEL_TITLE, PANEL_URL_PATH, STATIC_URL, DATA_DEBUG_RF, DATA_DEBUG_QRF, DATA_LAST_COMMAND, DATA_LAST_ERROR, DATA_LAST_RESULT, DATA_LAST_UPDATED
from .helpers import async_check_rflink_status, async_check_version_support, async_install_rflink_yaml, async_remove_rflink_yaml, async_send_protocol_command, async_send_raw_command, async_set_debug
from .aliases import SIGNAL_ALIASES_UPDATED, async_delete_alias, async_list_aliases, async_save_alias
from .firmware_lab import async_capture_firmware_button, async_clear_firmware_lab, async_delete_firmware_capture, async_get_firmware_lab, async_start_firmware_lab, async_stop_firmware_lab, async_update_firmware_lab, export_firmware_lab_report
from .settings import SIGNAL_OPTIONS_UPDATED, async_get_options, async_install_home_card, async_remove_home_card, async_set_options

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Any(None, vol.Schema({}))}, extra=vol.ALLOW_EXTRA)
SEND_RAW_SCHEMA = vol.Schema({vol.Required('raw_command'): cv.string, vol.Optional('repeat', default=1): vol.Coerce(int), vol.Optional('delay_ms', default=250): vol.Coerce(int)})
SEND_PROTOCOL_SCHEMA = vol.Schema({vol.Required(CONF_DEVICE_ID): cv.string, vol.Required(CONF_COMMAND): cv.string, vol.Optional('repeat', default=1): vol.Coerce(int), vol.Optional('delay_ms', default=250): vol.Coerce(int)})
SET_DEBUG_SCHEMA = vol.Schema({vol.Required('debug_type'): vol.In(['rfdebug','qrfdebug']), vol.Required('enabled'): cv.boolean})
INSTALL_RFLINK_SCHEMA = vol.Schema({vol.Optional('port', default='/dev/ttyUSB0'): cv.string})
SET_OPTIONS_SCHEMA = vol.Schema({vol.Optional('sidebar_enabled'): cv.boolean, vol.Optional('alias_switches_enabled'): cv.boolean, vol.Optional('home_card_enabled'): cv.boolean})
PLATFORMS = [Platform.SWITCH]


def _is_unknown(value: Any) -> bool:
    return str(value or '').strip() in {'Unknown command.', 'Unknown command'}


def _sanitize(hass: HomeAssistant) -> None:
    data = hass.data.setdefault(DOMAIN, {})
    if _is_unknown(data.get(DATA_LAST_ERROR)): data[DATA_LAST_ERROR] = ''
    if _is_unknown(data.get(DATA_LAST_RESULT)): data[DATA_LAST_RESULT] = ''


def _clear(hass: HomeAssistant) -> None:
    data = hass.data.setdefault(DOMAIN, {})
    data[DATA_LAST_RESULT] = ''; data[DATA_LAST_ERROR] = ''; data[DATA_LAST_COMMAND] = ''; data[DATA_LAST_UPDATED] = ''


def _rflink_connected() -> bool:
    try:
        from homeassistant.components.rflink.entity import RflinkCommand
        return bool(RflinkCommand.is_connected())
    except Exception:
        return False


def _rflink_configured(hass: HomeAssistant) -> bool:
    try: text = Path(hass.config.path('configuration.yaml')).read_text(errors='ignore')
    except Exception: return False
    return bool(re.search(r'(?m)^rflink:\s*(?:#.*)?$', text))


async def _status_payload(hass: HomeAssistant) -> dict[str, Any]:
    _sanitize(hass)
    data = hass.data.setdefault(DOMAIN, {})
    configured = _rflink_configured(hass); loaded = 'rflink' in hass.config.components; connected = _rflink_connected()
    if connected:
        readiness, detail = 'ready', 'Home Assistant RFLink command bridge reports connected.'
    elif loaded:
        readiness, detail = 'loaded', 'Home Assistant loaded RFLink. Use Captured to inspect entities/logs or Send with a learned command.'
    elif configured:
        readiness, detail = 'configured_needs_restart', 'RFLink is in configuration.yaml but is not loaded. Restart Home Assistant Core.'
    else:
        readiness, detail = 'not_configured', 'Use Configuration -> Install RFLink YAML, then restart Home Assistant Core.'
    options = await async_get_options(hass)
    return {'version': VERSION, 'name': NAME, 'rflink_configured': configured, 'rflink_loaded': loaded, 'rflink_connected': connected, 'readiness': readiness, 'readiness_detail': detail, 'last_result': data.get(DATA_LAST_RESULT,''), 'last_error': data.get(DATA_LAST_ERROR,''), 'last_command': data.get(DATA_LAST_COMMAND,''), 'last_updated': data.get(DATA_LAST_UPDATED,''), 'rfdebug': bool(data.get(DATA_DEBUG_RF, False)), 'qrfdebug': bool(data.get(DATA_DEBUG_QRF, False)), 'options': options}


def _split_entity_device_key(entity_id: str) -> dict[str, Any]:
    suffix = entity_id.split('.', 1)[-1]
    parts = suffix.split('_')
    protocol = parts[0] if parts else suffix
    address = parts[1] if len(parts) >= 2 else ''
    switch = ''
    sensor_suffixes = {'current','update','time','volt','voltage','watt','temperature','humidity','battery','status'}
    if len(parts) >= 3 and parts[-1].lower() not in sensor_suffixes:
        switch = parts[-1]
    return {'device_key': suffix, 'protocol': protocol, 'address': address, 'switch': switch}


def _entity_candidates(entity_id: str, domain: str) -> dict[str, str]:
    parsed = _split_entity_device_key(entity_id)
    protocol = parsed['protocol']
    address = parsed['address']
    switch = parsed['switch']
    if domain not in {'light', 'switch'} or not protocol or not address:
        return {}
    device_id = (f"{protocol}_{address}_{switch}" if switch else f"{protocol}_{address}").lower()
    return {'on': f'{device_id};on', 'off': f'{device_id};off', 'device_id': device_id}


def _parse_rflink_packet(line: str) -> dict[str, str]:
    match = re.search(r'\b((?:10|20);[^\r\n]+)', line)
    raw_packet = ''
    send_candidate = ''
    protocol = ''
    command = ''
    if match:
        raw_packet = match.group(1).strip().strip(' "\'')
        raw_packet = raw_packet.rstrip(' "\'')
        parts = [p for p in raw_packet.split(';') if p != '']
        if len(parts) >= 3 and parts[0] == '20':
            protocol = parts[2]
            values = {}
            for token in parts[3:]:
                if '=' in token:
                    k, v = token.split('=', 1)
                    values[k.strip().upper()] = v.strip()
            rf_id = values.get('ID') or values.get('UNIT') or values.get('ADDRESS') or values.get('CODE') or ''
            switch = values.get('SWITCH') or values.get('CHANNEL') or ''
            command = values.get('CMD') or values.get('COMMAND') or ''
            if protocol and rf_id and command:
                send_candidate = f'10;{protocol};{rf_id};{switch + ";" if switch else ""}{command};'
        elif len(parts) >= 2 and parts[0] == '10':
            protocol = parts[1]
            command = parts[-1] if len(parts) >= 3 else ''
            send_candidate = raw_packet if raw_packet.endswith(';') else raw_packet + ';'
    return {'raw_packet': raw_packet, 'send_candidate': send_candidate, 'protocol': protocol, 'command': command}


def _read_logs(hass: HomeAssistant, max_lines: int = 120) -> list[dict[str,str]]:
    path = Path(hass.config.path('home-assistant.log'))
    if not path.exists():
        return []
    out = []
    for line in path.read_text(errors='ignore').splitlines()[-5000:]:
        low = line.lower()
        if 'rflink' not in low and '433' not in low:
            continue
        if 'unknown command' in low:
            continue
        parsed = _parse_rflink_packet(line)
        out.append({'line': line[-900:], 'command': parsed['send_candidate'], 'raw_packet': parsed['raw_packet'], 'send_candidate': parsed['send_candidate'], 'protocol': parsed['protocol'], 'packet_command': parsed['command']})
    return out[-max_lines:]


def _entities(hass: HomeAssistant) -> list[dict[str,Any]]:
    reg = er.async_get(hass)
    items = []
    for state in hass.states.async_all():
        entry = reg.async_get(state.entity_id)
        if not entry or entry.platform != 'rflink':
            continue
        domain = state.entity_id.split('.', 1)[0]
        parsed = _split_entity_device_key(state.entity_id)
        candidates = _entity_candidates(state.entity_id, domain)
        items.append({'entity_id': state.entity_id, 'name': state.name, 'state': state.state, 'domain': domain, 'unique_id': entry.unique_id, 'device_id': entry.device_id, 'device_key': parsed['device_key'], 'protocol': parsed['protocol'], 'address': parsed['address'], 'switch': parsed['switch'], 'candidate_on': candidates.get('on', ''), 'candidate_off': candidates.get('off', ''), 'send_device_id': candidates.get('device_id', '')})
    return sorted(items, key=lambda x: x['entity_id'])


@callback
def _websocket_status(hass: HomeAssistant, connection, msg) -> None:
    async def _send() -> None:
        connection.send_result(msg['id'], await _status_payload(hass))
    hass.async_create_task(_send())


class RFLinkRawAliasesView(HomeAssistantView):
    url='/api/rflink_raw/aliases'; name='api:rflink_raw:aliases'; requires_auth=True

    async def get(self, request):
        hass = request.app['hass']
        aliases = await async_list_aliases(hass)
        return self.json({'aliases': aliases})

    async def post(self, request):
        hass = request.app['hass']
        data = await request.json()
        if data.get('delete'):
            aliases = await async_delete_alias(hass, data.get('id', ''))
            async_dispatcher_send(hass, SIGNAL_ALIASES_UPDATED)
            return self.json({'ok': True, 'aliases': aliases})
        alias = await async_save_alias(hass, data)
        async_dispatcher_send(hass, SIGNAL_ALIASES_UPDATED)
        aliases = await async_list_aliases(hass)
        return self.json({'ok': True, 'alias': alias, 'aliases': aliases})


class RFLinkRawFirmwareLabView(HomeAssistantView):
    url='/api/rflink_raw/firmware_lab'; name='api:rflink_raw:firmware_lab'; requires_auth=True

    async def get(self, request):
        hass = request.app['hass']
        lab = await async_get_firmware_lab(hass)
        return self.json({'lab': lab, 'report': export_firmware_lab_report(lab)})

    async def post(self, request):
        hass = request.app['hass']
        data = await request.json()
        action = str(data.get('action') or 'update').strip().lower()
        if action == 'start':
            await async_set_debug(hass, 'qrfdebug', True)
            lab = await async_start_firmware_lab(hass, data.get('project_name', ''), data.get('notes', ''), bool(data.get('reset')))
        elif action == 'stop':
            await async_set_debug(hass, 'qrfdebug', False)
            lab = await async_stop_firmware_lab(hass)
        elif action == 'capture':
            lab = await async_capture_firmware_button(hass, data.get('label', ''), data.get('notes', ''))
        elif action == 'delete_capture':
            lab = await async_delete_firmware_capture(hass, data.get('id', ''))
        elif action == 'clear':
            lab = await async_clear_firmware_lab(hass)
        else:
            lab = await async_update_firmware_lab(hass, data)
        return self.json({'ok': True, 'lab': lab, 'report': export_firmware_lab_report(lab)})


class RFLinkRawStatusView(HomeAssistantView):
    url='/api/rflink_raw/status'; name='api:rflink_raw:status'; requires_auth=True
    async def get(self, request): return self.json(await _status_payload(request.app['hass']))


class RFLinkRawEntitiesView(HomeAssistantView):
    url='/api/rflink_raw/entities'; name='api:rflink_raw:entities'; requires_auth=True
    async def get(self, request): return self.json({'entities': _entities(request.app['hass'])})


class RFLinkRawLogsView(HomeAssistantView):
    url='/api/rflink_raw/logs'; name='api:rflink_raw:logs'; requires_auth=True
    async def get(self, request):
        hass = request.app['hass']; lines = await hass.async_add_executor_job(_read_logs, hass)
        return self.json({'lines': lines})


class RFLinkRawOptionsView(HomeAssistantView):
    url='/api/rflink_raw/options'; name='api:rflink_raw:options'; requires_auth=True

    async def get(self, request):
        return self.json({'options': await async_get_options(request.app['hass'])})

    async def post(self, request):
        hass = request.app['hass']
        data = await request.json()
        action = str(data.get('action') or 'set').strip().lower()
        result: dict[str, Any] = {'ok': True}
        if action == 'install_home_card':
            result = await async_install_home_card(hass)
        elif action == 'remove_home_card':
            result = await async_remove_home_card(hass)
        else:
            updates = {k: data[k] for k in ('sidebar_enabled','alias_switches_enabled','home_card_enabled') if k in data}
            if updates:
                await async_set_options(hass, updates)
                if 'sidebar_enabled' in updates:
                    await _async_register_panel(hass, visible=bool(updates['sidebar_enabled']))
                async_dispatcher_send(hass, SIGNAL_OPTIONS_UPDATED)
        options = await async_get_options(hass)
        async_dispatcher_send(hass, SIGNAL_OPTIONS_UPDATED)
        return self.json({'ok': True, 'options': options, 'result': result})


async def _async_register_panel(hass: HomeAssistant, visible: bool | None = None) -> None:
    await hass.http.async_register_static_paths([StaticPathConfig(STATIC_URL, str(Path(__file__).parent/'www'), False)])
    if visible is None:
        options = await async_get_options(hass)
        visible = bool(options.get('sidebar_enabled', True))
    async_remove_panel(hass, PANEL_URL_PATH)
    sidebar_title = PANEL_TITLE if visible else None
    sidebar_icon = PANEL_ICON if visible else None
    async_register_built_in_panel(hass, component_name='custom', sidebar_title=sidebar_title, sidebar_icon=sidebar_icon, frontend_url_path=PANEL_URL_PATH, require_admin=False, config={'_panel_custom': {'name': 'rflink-raw-tools-panel', 'module_url': PANEL_MODULE, 'embed_iframe': False}})


async def _async_register_backend(hass: HomeAssistant) -> None:
    data = hass.data.setdefault(DOMAIN, {})
    if not data.get('_views_registered'):
        for view in (RFLinkRawStatusView, RFLinkRawEntitiesView, RFLinkRawLogsView, RFLinkRawAliasesView, RFLinkRawFirmwareLabView, RFLinkRawOptionsView):
            try: hass.http.register_view(view)
            except Exception: pass
        data['_views_registered'] = True
    if data.get('_backend_registered'): return
    async def send_raw(call: ServiceCall) -> None: await async_send_raw_command(hass, call.data['raw_command'], call.data['repeat'], call.data['delay_ms'])
    async def send_protocol(call: ServiceCall) -> None: await async_send_protocol_command(hass, call.data[CONF_DEVICE_ID], call.data[CONF_COMMAND], call.data['repeat'], call.data['delay_ms'])
    async def check_status(call: ServiceCall) -> None: await async_check_rflink_status(hass)
    async def version_gateway(call: ServiceCall) -> None: await async_check_version_support(hass)
    async def set_debug(call: ServiceCall) -> None: await async_set_debug(hass, call.data['debug_type'], call.data['enabled'])
    async def clear_status(call: ServiceCall) -> None: _clear(hass)
    async def install_rflink_yaml(call: ServiceCall) -> None: await async_install_rflink_yaml(hass, call.data['port'])
    async def remove_rflink_yaml(call: ServiceCall) -> None: await async_remove_rflink_yaml(hass)
    async def set_options(call: ServiceCall) -> None:
        options = await async_set_options(hass, dict(call.data))
        if 'sidebar_enabled' in call.data:
            await _async_register_panel(hass, visible=bool(options.get('sidebar_enabled', True)))
        async_dispatcher_send(hass, SIGNAL_OPTIONS_UPDATED)
    async def install_home_card(call: ServiceCall) -> None:
        await async_install_home_card(hass); async_dispatcher_send(hass, SIGNAL_OPTIONS_UPDATED)
    async def remove_home_card(call: ServiceCall) -> None:
        await async_remove_home_card(hass); async_dispatcher_send(hass, SIGNAL_OPTIONS_UPDATED)
    _clear(hass)
    hass.services.async_register(DOMAIN, 'send_raw', send_raw, schema=SEND_RAW_SCHEMA)
    hass.services.async_register(DOMAIN, 'send_protocol', send_protocol, schema=SEND_PROTOCOL_SCHEMA)
    hass.services.async_register(DOMAIN, 'ping_gateway', check_status)
    hass.services.async_register(DOMAIN, 'version_gateway', version_gateway)
    hass.services.async_register(DOMAIN, 'set_debug', set_debug, schema=SET_DEBUG_SCHEMA)
    hass.services.async_register(DOMAIN, 'clear_status', clear_status)
    hass.services.async_register(DOMAIN, 'install_rflink_yaml', install_rflink_yaml, schema=INSTALL_RFLINK_SCHEMA)
    hass.services.async_register(DOMAIN, 'remove_rflink_yaml', remove_rflink_yaml)
    hass.services.async_register(DOMAIN, 'set_options', set_options, schema=SET_OPTIONS_SCHEMA)
    hass.services.async_register(DOMAIN, 'install_home_card', install_home_card)
    hass.services.async_register(DOMAIN, 'remove_home_card', remove_home_card)
    websocket_api.async_register_command(hass, _websocket_status, websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend({vol.Required('type'): 'rflink_raw/status'}))
    data['_backend_registered'] = True


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    await _async_register_backend(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    await _async_register_backend(hass)
    await _async_register_panel(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    async_remove_panel(hass, PANEL_URL_PATH)
    return unload_ok
