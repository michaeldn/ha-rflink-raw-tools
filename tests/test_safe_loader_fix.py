from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
CC = ROOT / "custom_components/rflink_raw"
INIT = CC / "__init__.py"
HELPERS = CC / "helpers.py"
PANEL = CC / "www/rflink-raw-tools-panel.js"
MANIFEST = CC / "manifest.json"
INSTALL = ROOT / "install.sh"

def test_experimental_switch_platform_disabled():
    init = INIT.read_text()
    manifest = json.loads(MANIFEST.read_text())
    assert not (CC / "switch.py").exists()
    assert "async_forward_entry_setups(entry, ['switch'])" not in init
    assert "async_unload_platforms(entry, ['switch'])" not in init
    assert "switch" not in manifest.get("after_dependencies", [])

def test_setup_helpers_and_input_stability():
    helpers = HELPERS.read_text()
    panel = PANEL.read_text()
    assert "def _config_has_rflink" in helpers
    assert "def _install_yaml" in helpers
    assert 'APP_BUILD_ID = "safe-loader-fix-20260512"' in panel
    assert "_setLabField(f,v){this._state.firmwareLab={...(this._state.firmwareLab||{}),[f]:v};}" in panel
    assert "_setFirmwareField(f,v){this._state[f]=v;}" in panel
    assert "_setTeachField(f,v){this._state.teach={...(this._state.teach||{}),[f]:v};}" in panel

def test_installer_no_auto_restart():
    install = INSTALL.read_text()
    assert "ha core restart" not in install
    assert "Core was NOT restarted" in install

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
