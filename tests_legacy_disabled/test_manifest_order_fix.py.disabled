import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_manifest_keys_follow_hassfest_order():
    manifest = json.loads((ROOT / "custom_components/rflink_raw/manifest.json").read_text())
    keys = list(manifest.keys())
    expected = ["domain", "name"] + sorted(key for key in keys if key not in {"domain", "name"})
    assert keys == expected
    assert manifest["domain"] == "rflink_raw"
    assert manifest["name"] == "RFLink Raw Tools"
    assert manifest["version"] == "0.0.1"

def test_hassfest_dependencies_preserved():
    manifest = json.loads((ROOT / "custom_components/rflink_raw/manifest.json").read_text())
    deps = set(manifest.get("after_dependencies", []))
    assert {"frontend", "http", "rflink", "websocket_api"}.issubset(deps)

def test_hacs_json_schema_still_valid():
    hacs = json.loads((ROOT / "hacs.json").read_text())
    assert "domains" not in hacs
    assert hacs["name"] == "RFLink Raw Tools"

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
