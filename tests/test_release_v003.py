import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CC = ROOT / "custom_components" / "rflink_raw"
PANEL = CC / "www" / "rflink-raw-tools-panel.js"
CONST = CC / "const.py"
MANIFEST = CC / "manifest.json"
SETTINGS = CC / "settings.py"
INIT = CC / "__init__.py"


def test_manifest_and_build_are_v003():
    manifest = json.loads(MANIFEST.read_text())
    const = CONST.read_text()
    panel = PANEL.read_text()

    assert manifest["domain"] == "rflink_raw"
    assert manifest["name"] == "RFLink Raw Tools"
    assert manifest["version"] == "0.0.5"

    assert 'VERSION = "0.0.5"' in const
    assert 'PANEL_BUILD = "v005-release-workflow-fix-20260518"' in const
    assert 'APP_BUILD_ID = "v005-release-workflow-fix-20260518"' in panel
    assert "?v={PANEL_BUILD}" in const


def test_v003_app_structure_is_present():
    panel = PANEL.read_text()

    assert 'data-tab="info">Info' in panel
    assert 'data-tab="configuration">Configuration' in panel
    assert 'data-tab="log">Log' in panel

    assert "RFLink YAML" in panel
    assert "Alias-backed HA switches" in panel
    assert "Raw RF capture logging" in panel
    assert "Decoded RFLink logging" in panel
    assert "RFLink Tools" in panel
    assert "Teach Alias" in panel


def test_dashboard_shortcut_is_manual_not_auto_overview_editing():
    panel = PANEL.read_text()
    settings = SETTINGS.read_text()

    assert "Dashboard shortcut" in panel
    assert "Copy card YAML" in panel
    assert "Open Overview" in panel
    assert "Open RFLink Raw Tools" in panel
    assert "RFLink Raw Tools does not edit Overview automatically in v0.0.5" in panel

    assert 'data-action="_installHomeCard"' not in panel
    assert 'data-action="_removeHomeCard"' not in panel
    assert "Add to Overview" not in panel
    assert "Remove from Overview" not in panel

    assert "Automatic Overview dashboard editing was removed in v0.0.5" in settings
    assert "_install_overview_card" not in settings
    assert "_remove_overview_card" not in settings


def test_sidebar_alias_switch_and_backend_are_present():
    init = INIT.read_text()
    switch_file = CC / "switch.py"

    assert "RFLinkRawStatusView" in init
    assert "/api/rflink_raw/status" in init
    assert "RFLinkRawOptionsView" in init
    assert "_async_register_panel" in init
    assert "async_forward_entry_setups" in init

    assert switch_file.exists()
    switch_text = switch_file.read_text()
    assert "RFLinkAliasSwitch" in switch_text
    assert "async_send_raw_command" in switch_text


def test_release_files_have_no_tracked_cache_artifacts():
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    tracked = result.stdout.splitlines()
    assert not any("__pycache__" in p for p in tracked)
    assert not any(p.endswith(".pyc") for p in tracked)
    assert not any(p.startswith(".venv/") for p in tracked)


def test_icon_paths_exist_without_asserting_artwork_hash():
    paths = [
        ROOT / "assets/icon.png",
        ROOT / "assets/logo.png",
        ROOT / "icon.png",
        ROOT / "logo.png",
        CC / "icon.png",
        CC / "logo.png",
        CC / "brand/icon.png",
        CC / "brand/logo.png",
        CC / "www/icon.png",
        CC / "www/logo.png",
    ]

    for path in paths:
        assert path.exists(), path
        assert path.stat().st_size > 0, path
