from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPERS = ROOT / "custom_components/rflink_raw/helpers.py"
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"

def test_setup_helpers_exist():
    text = HELPERS.read_text()
    assert "def _config_has_rflink" in text
    assert "def _install_yaml" in text
    assert "async_check_rflink_status" in text
    assert "_config_has_rflink" in text

def test_typing_handlers_do_not_rerender_on_every_keypress():
    text = PANEL.read_text()
    assert 'APP_BUILD_ID = "setup-input-stability-fix-20260512"' in text
    assert "_setLabField(f,v){this._state.firmwareLab={...(this._state.firmwareLab||{}),[f]:v};}" in text
    assert "_setFirmwareField(f,v){this._state[f]=v;}" in text
    assert "_setTeachField(f,v){this._state.teach={...(this._state.teach||{}),[f]:v};}" in text
    assert "_setLabField(f,v){this._state.firmwareLab={...(this._state.firmwareLab||{}),[f]:v};this._update();}" not in text
    assert "_setFirmwareField(f,v){this._state[f]=v;this._update();}" not in text

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
