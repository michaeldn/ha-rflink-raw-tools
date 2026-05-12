from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "custom_components/rflink_raw/__init__.py"
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"
ALIASES = ROOT / "custom_components/rflink_raw/aliases.py"
SWITCH = ROOT / "custom_components/rflink_raw/switch.py"
MANIFEST = ROOT / "custom_components/rflink_raw/manifest.json"

def test_alias_backend_and_switch_platform_exist():
    assert ALIASES.exists()
    assert SWITCH.exists()
    init = INIT.read_text()
    assert "RFLinkRawAliasesView" in init
    assert "/api/rflink_raw/aliases" in init
    assert "async_forward_entry_setups(entry, ['switch'])" in init
    manifest = json.loads(MANIFEST.read_text())
    assert "switch" in manifest.get("after_dependencies", [])

def test_teach_tab_frontend_exists():
    text = PANEL.read_text()
    assert 'APP_BUILD_ID = "teach-alias-feature-20260512"' in text
    assert 'data-tab="teach"' in text
    assert "_teachView()" in text
    assert "_saveAlias()" in text
    assert "Teach as device" in text
    assert "Saved aliases" in text

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
