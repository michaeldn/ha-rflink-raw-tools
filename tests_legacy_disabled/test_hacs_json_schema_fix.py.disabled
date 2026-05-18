import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_hacs_json_uses_supported_keys_only():
    hacs = json.loads((ROOT / "hacs.json").read_text())
    assert hacs["name"] == "RFLink Raw Tools"
    assert hacs["render_readme"] is True
    assert hacs["homeassistant"] == "2024.8.0"
    assert hacs["content_in_root"] is False
    assert "domains" not in hacs

def test_manifest_still_declares_integration_domain_and_dependencies():
    manifest = json.loads((ROOT / "custom_components/rflink_raw/manifest.json").read_text())
    assert manifest["domain"] == "rflink_raw"
    assert manifest["version"] == "0.0.1"
    deps = set(manifest.get("after_dependencies", []))
    assert {"frontend", "http", "rflink", "websocket_api"}.issubset(deps)

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
