import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_manifest_declares_optional_component_dependencies():
    manifest = json.loads((ROOT / "custom_components/rflink_raw/manifest.json").read_text())
    deps = set(manifest.get("after_dependencies", []))
    assert "http" in deps
    assert "frontend" in deps
    assert "websocket_api" in deps
    assert "rflink" in deps
    assert "rflink" not in set(manifest.get("dependencies", []))

def test_workflows_opt_into_node24():
    for path in (ROOT / ".github/workflows").glob("*.yml"):
        text = path.read_text()
        assert "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true" in text

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
