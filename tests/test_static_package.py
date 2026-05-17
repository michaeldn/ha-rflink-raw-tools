from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def test_no_button_or_cache_artifacts():
    assert not (ROOT / "custom_components/rflink_raw/button.py").exists()
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))

def test_manifest_version_and_config_flow():
    manifest = json.loads((ROOT / "custom_components/rflink_raw/manifest.json").read_text())
    assert manifest["domain"] == "rflink_raw"
    assert manifest["version"] == "0.0.2"
    assert manifest["config_flow"] is True

def test_app_panel_exists():
    app = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"
    assert app.exists()
    text = app.read_text()
    assert "customElements.define" in text
    assert "rflink-raw-tools-panel" in text

def test_no_generated_lovelace_dashboard():
    assert not (ROOT / "dashboard/rflink_raw_dashboard.yaml").exists()


def test_alias_switch_platform_exists():
    switch_file = ROOT / "custom_components/rflink_raw/switch.py"
    assert switch_file.exists()
    text = switch_file.read_text()
    assert "RFLinkAliasSwitch" in text
    assert "async_send_raw_command" in text
