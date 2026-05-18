from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPERS = ROOT / "custom_components/rflink_raw/helpers.py"
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"

def test_debug_switches_do_not_send_gateway_commands():
    text = HELPERS.read_text()
    func = text.split("async def async_set_debug", 1)[1]
    assert "_set_rflink_logger_level(hass, bool(enabled))" in func
    assert "gateway_command_sent" in func
    assert "False" in func
    assert "_call_rflink_send_command_service(hass, kind, command)" not in func

def test_ui_explains_logger_not_gateway_command():
    text = PANEL.read_text()
    assert 'APP_BUILD_ID = "debug-logger-fix-20260512"' in text
    assert "does not send rfdebug/qrfdebug commands to the gateway" in text

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
