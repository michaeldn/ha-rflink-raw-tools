from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"
HELPERS = ROOT / "custom_components/rflink_raw/helpers.py"

def test_fake_examples_are_not_clickable():
    text = PANEL.read_text()
    assert 'APP_BUILD_ID = "send-examples-cleanup-20260512"' in text
    start = text.find("_sendView(){")
    end = text.find("_capturedView(){", start)
    send_view = text[start:end]
    assert "data-copy-command=\"10;NewKaku;01a2b3" not in send_view
    assert "Accepted command formats" in send_view
    assert "Documentation only" in send_view
    assert "Paste from Captured" in send_view

def test_parser_lowercases_ha_device_id():
    text = HELPERS.read_text()
    assert "return device_id.lower(), action" in text or "device_id = device_id.lower()" in text

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
