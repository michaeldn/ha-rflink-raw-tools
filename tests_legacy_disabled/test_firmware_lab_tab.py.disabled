from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "custom_components/rflink_raw/__init__.py"
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"
LAB = ROOT / "custom_components/rflink_raw/firmware_lab.py"

def test_firmware_lab_backend_exists():
    assert LAB.exists()
    lab = LAB.read_text()
    assert "rflink_raw_firmware_lab.json" in lab
    assert "async_capture_firmware_button" in lab
    assert "export_firmware_lab_report" in lab
    init = INIT.read_text()
    assert "RFLinkRawFirmwareLabView" in init
    assert "/api/rflink_raw/firmware_lab" in init
    assert "async_set_debug(hass, 'qrfdebug', True)" in init

def test_firmware_lab_frontend_exists():
    text = PANEL.read_text()
    assert 'APP_BUILD_ID = "firmware-lab-tab-20260512"' in text
    assert 'data-tab="firmware"' in text
    assert "_firmwareView()" in text
    assert "Start RF debug capture" in text
    assert "Button/capture name" in text
    assert "anything you want" in text
    assert "_downloadFirmwareReport" in text

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
