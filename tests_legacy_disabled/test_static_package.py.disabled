from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))


def test_manifest_version_and_switch_dependency():
    manifest = json.loads((ROOT / "custom_components/rflink_raw/manifest.json").read_text())
    assert manifest["domain"] == "rflink_raw"
    assert manifest["version"] == "0.0.3"
    assert manifest["config_flow"] is True
    assert "switch" in manifest["after_dependencies"]


def test_app_panel_exists():
    app = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"
    assert app.exists()
    text = app.read_text()
    assert "customElements.define" in text
    assert "rflink-raw-tools-panel" in text
    assert "Info" in text
    assert "Configuration" in text
    assert "Log" in text


def test_alias_switch_platform_exists():
    switch_file = ROOT / "custom_components/rflink_raw/switch.py"
    assert switch_file.exists()
    text = switch_file.read_text()
    assert "RFLinkAliasSwitch" in text
    assert "async_send_raw_command" in text


def test_settings_and_yaml_removal_exist():
    assert (ROOT / "custom_components/rflink_raw/settings.py").exists()
    helpers = (ROOT / "custom_components/rflink_raw/helpers.py").read_text()
    assert "async_remove_rflink_yaml" in helpers
