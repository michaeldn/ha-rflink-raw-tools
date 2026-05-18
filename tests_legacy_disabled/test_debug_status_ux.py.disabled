from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPERS = ROOT / "custom_components/rflink_raw/helpers.py"
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"

def test_debug_helpers_do_not_throw_for_set_debug_paths():
    text = HELPERS.read_text()
    block = text.split("async def async_set_debug", 1)[1]
    assert "return {" in block
    assert "local_state" in block
    assert "_set_status(hass, result=message" in block

def test_debug_switch_ui_has_enabled_disabled_and_build_id():
    text = PANEL.read_text()
    assert 'APP_BUILD_ID = "debug-status-ux-fix-20260510"' in text
    assert 'status.rfdebug ? "Enabled" : "Disabled"' in text
    assert 'status.qrfdebug ? "Enabled" : "Disabled"' in text
    assert "RFLink configuration scan" in text
