from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "custom_components/rflink_raw/__init__.py"
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"
HELPERS = ROOT / "custom_components/rflink_raw/helpers.py"

def test_status_api_backend_exists():
    text = INIT.read_text()
    assert "class RFLinkRawStatusView" in text
    assert 'url = "/api/rflink_raw/status"' in text
    assert "hass.http.register_view(RFLinkRawStatusView)" in text
    assert "def _sanitize_status_data" in text

def test_clean_frontend_app_ux():
    text = PANEL.read_text()
    assert 'APP_BUILD_ID = "software-cleanup-final-20260511"' in text
    assert 'callApi("GET", "rflink_raw/status")' in text
    assert 'callWS' not in text.split("async _loadStatus", 1)[1].split("_formatError", 1)[0]
    assert 'data-tab="capture"' in text
    assert "Capture a remote command" in text
    assert "Decoded RFLink logging" in text
    assert "Raw RF capture logging" in text
    assert "Unknown command." not in text.replace('String(value || "").trim() === "Unknown command."', "")

def test_diagnostic_helpers_do_not_throw_for_ping_version_debug():
    text = HELPERS.read_text()
    ping = text.split("async def async_ping_gateway", 1)[1].split("async def async_version_gateway", 1)[0]
    version = text.split("async def async_version_gateway", 1)[1].split("async def async_set_debug", 1)[0]
    debug = text.split("async def async_set_debug", 1)[1]
    assert "raise HomeAssistantError" not in ping
    assert "raise HomeAssistantError" not in version
    assert "local_state" in debug
