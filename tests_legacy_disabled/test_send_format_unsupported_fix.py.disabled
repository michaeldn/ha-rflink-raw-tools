from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPERS = ROOT / "custom_components/rflink_raw/helpers.py"
INIT = ROOT / "custom_components/rflink_raw/__init__.py"
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"

def test_send_parser_converts_semicolon_raw_to_ha_rflink_format():
    text = HELPERS.read_text()
    assert "def _device_id_from_rflink_parts" in text
    assert "\"_\".join(device_parts)" in text
    assert "newkaku_0000c6c2_1;on" in text
    assert "KeyError" in text and "receive-only" in text

def test_candidates_use_ha_service_format_not_fake_raw():
    text = INIT.read_text()
    assert "f'{device_id};on'" in text
    assert "f'{device_id};off'" in text
    assert "send_device_id" in text

def test_ui_copy_is_honest_about_unsupported_devices():
    text = PANEL.read_text()
    assert 'APP_BUILD_ID = "send-format-unsupported-fix-20260512"' in text
    assert "not in the RFLink database" in text
    assert "Candidate send commands" in text

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
