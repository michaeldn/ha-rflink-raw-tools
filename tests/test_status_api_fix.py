from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "custom_components/rflink_raw/__init__.py"
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"

def test_backend_status_api_view_registered():
    text = INIT.read_text()
    assert "class RFLinkRawStatusView" in text
    assert 'url = "/api/rflink_raw/status"' in text
    assert "hass.http.register_view(RFLinkRawStatusView)" in text
    assert "def _sanitize_status_data" in text
    assert "_sanitize_status_data(hass)" in text

def test_frontend_uses_callapi_not_ws_for_status():
    text = PANEL.read_text()
    load = text.split("async _loadStatus", 1)[1].split("_formatError", 1)[0]
    assert 'callApi("GET", "rflink_raw/status")' in load
    assert "callWS" not in load
    assert "status_api_unavailable" in load
    assert 'this._state.error = ""' in load
    assert 'APP_BUILD_ID = "status-api-fix-20260510"' in text
