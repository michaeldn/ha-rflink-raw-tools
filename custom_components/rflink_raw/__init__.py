"""RFLink Raw Tools app-first integration."""
from __future__ import annotations
from pathlib import Path
import re
from typing import Any
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.components.frontend import async_register_built_in_panel, async_remove_panel
from homeassistant.components.http import HomeAssistantView, StaticPathConfig
from homeassistant.const import CONF_COMMAND, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN, NAME, VERSION, PANEL_ICON, PANEL_MODULE, PANEL_TITLE, PANEL_URL_PATH, STATIC_URL, DATA_DEBUG_RF, DATA_DEBUG_QRF, DATA_LAST_COMMAND, DATA_LAST_ERROR, DATA_LAST_RESULT, DATA_LAST_UPDATED
from .helpers import async_check_rflink_status, async_check_version_support, async_install_rflink_yaml, async_send_protocol_command, async_send_raw_command, async_set_debug

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Any(None, vol.Schema({}))}, extra=vol.ALLOW_EXTRA)
SEND_RAW_SCHEMA = vol.Schema({vol.Required('raw_command'): cv.string, vol.Optional('repeat', default=1): vol.Coerce(int), vol.Optional('delay_ms', default=250): vol.Coerce(int)})
SEND_PROTOCOL_SCHEMA = vol.Schema({vol.Required(CONF_DEVICE_ID): cv.string, vol.Required(CONF_COMMAND): cv.string, vol.Optional('repeat', default=1): vol.Coerce(int), vol.Optional('delay_ms', default=250): vol.Coerce(int)})
SET_DEBUG_SCHEMA = vol.Schema({vol.Required('debug_type'): vol.In(['rfdebug','qrfdebug']), vol.Required('enabled'): cv.boolean})
INSTALL_RFLINK_SCHEMA = vol.Schema({vol.Optional('port', default='/dev/ttyUSB0'): cv.string})

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

def _status_payload(hass: HomeAssistant) -> dict[str, Any]:
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
        readiness, detail = 'not_configured', 'Use Setup -> Install RFLink YAML, then restart Home Assistant Core.'
    return {'version': VERSION, 'name': NAME, 'rflink_configured': configured, 'rflink_loaded': loaded, 'rflink_connected': connected, 'readiness': readiness, 'readiness_detail': detail, 'last_result': data.get(DATA_LAST_RESULT,''), 'last_error': data.get(DATA_LAST_ERROR,''), 'last_command': data.get(DATA_LAST_COMMAND,''), 'last_updated': data.get(DATA_LAST_UPDATED,''), 'rfdebug': bool(data.get(DATA_DEBUG_RF, False)), 'qrfdebug': bool(data.get(DATA_DEBUG_QRF, False))}

def _read_logs(hass: HomeAssistant, max_lines: int = 120) -> list[dict[str,str]]:
    path = Path(hass.config.path('home-assistant.log'))
    if not path.exists(): return []
    out=[]
    for line in path.read_text(errors='ignore').splitlines()[-3000:]:
        low=line.lower()
        if 'rflink' not in low and '433' not in low: continue
        if 'unknown command' in low: continue
        m = re.search(r'(10;[^\s]+;)', line)
        out.append({'line': line[-600:], 'command': m.group(1) if m else ''})
    return out[-max_lines:]

def _entities(hass: HomeAssistant) -> list[dict[str,Any]]:
    reg = er.async_get(hass); items=[]
    for state in hass.states.async_all():
        entry = reg.async_get(state.entity_id)
        if not entry or entry.platform != 'rflink': continue
        items.append({'entity_id': state.entity_id, 'name': state.name, 'state': state.state, 'domain': state.entity_id.split('.',1)[0], 'unique_id': entry.unique_id, 'device_id': entry.device_id})
    return sorted(items, key=lambda x: x['entity_id'])

@callback
def _websocket_status(hass: HomeAssistant, connection, msg) -> None:
    connection.send_result(msg['id'], _status_payload(hass))

class RFLinkRawStatusView(HomeAssistantView):
    url='/api/rflink_raw/status'; name='api:rflink_raw:status'; requires_auth=True
    async def get(self, request): return self.json(_status_payload(request.app['hass']))
class RFLinkRawEntitiesView(HomeAssistantView):
    url='/api/rflink_raw/entities'; name='api:rflink_raw:entities'; requires_auth=True
    async def get(self, request): return self.json({'entities': _entities(request.app['hass'])})
class RFLinkRawLogsView(HomeAssistantView):
    url='/api/rflink_raw/logs'; name='api:rflink_raw:logs'; requires_auth=True
    async def get(self, request):
        hass = request.app['hass']; lines = await hass.async_add_executor_job(_read_logs, hass)
        return self.json({'lines': lines})

async def _async_register_panel(hass: HomeAssistant) -> None:
    await hass.http.async_register_static_paths([StaticPathConfig(STATIC_URL, str(Path(__file__).parent/'www'), False)])
    async_remove_panel(hass, PANEL_URL_PATH)
    async_register_built_in_panel(hass, component_name='custom', sidebar_title=PANEL_TITLE, sidebar_icon=PANEL_ICON, frontend_url_path=PANEL_URL_PATH, require_admin=False, config={'_panel_custom': {'name': 'rflink-raw-tools-panel', 'module_url': PANEL_MODULE, 'embed_iframe': False}})

async def _async_register_backend(hass: HomeAssistant) -> None:
    data = hass.data.setdefault(DOMAIN, {})
    if not data.get('_views_registered'):
        for view in (RFLinkRawStatusView, RFLinkRawEntitiesView, RFLinkRawLogsView):
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
    _clear(hass)
    hass.services.async_register(DOMAIN, 'send_raw', send_raw, schema=SEND_RAW_SCHEMA)
    hass.services.async_register(DOMAIN, 'send_protocol', send_protocol, schema=SEND_PROTOCOL_SCHEMA)
    hass.services.async_register(DOMAIN, 'ping_gateway', check_status)
    hass.services.async_register(DOMAIN, 'version_gateway', version_gateway)
    hass.services.async_register(DOMAIN, 'set_debug', set_debug, schema=SET_DEBUG_SCHEMA)
    hass.services.async_register(DOMAIN, 'clear_status', clear_status)
    hass.services.async_register(DOMAIN, 'install_rflink_yaml', install_rflink_yaml, schema=INSTALL_RFLINK_SCHEMA)
    websocket_api.async_register_command(hass, _websocket_status, websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend({vol.Required('type'): 'rflink_raw/status'}))
    data['_backend_registered'] = True

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    await _async_register_backend(hass); return True
async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    await _async_register_backend(hass); await _async_register_panel(hass); return True
async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    async_remove_panel(hass, PANEL_URL_PATH); return True
