import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_manifest_has_hassfest_metadata():
    manifest = json.loads((ROOT / "custom_components/rflink_raw/manifest.json").read_text())
    assert manifest["domain"] == "rflink_raw"
    assert manifest["version"] == "0.0.1"
    assert manifest["integration_type"] == "hub"
    assert manifest["iot_class"] == "local_push"
    assert manifest["documentation"]
    assert manifest["issue_tracker"]
    assert manifest["codeowners"]

def test_static_workflow_cleans_pycache_after_compile():
    text = (ROOT / ".github/workflows/static-package.yml").read_text()
    assert "Compile Python without leaving cache artifacts" in text
    assert "find . -type d -name '__pycache__' -prune -exec rm -rf {} +" in text
    assert "find . -type f -name '*.pyc' -delete" in text

def test_hacs_and_hassfest_have_checkout():
    hacs = (ROOT / ".github/workflows/hacs.yml").read_text()
    hassfest = (ROOT / ".github/workflows/hassfest.yml").read_text()
    assert "actions/checkout@v4" in hacs
    assert "actions/checkout@v4" in hassfest
    assert "ignore: brands description topics" in hacs

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
