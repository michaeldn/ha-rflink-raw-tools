import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_hacs_metadata_and_workflows():
    hacs = json.loads((ROOT / "hacs.json").read_text())
    manifest = json.loads((ROOT / "custom_components/rflink_raw/manifest.json").read_text())

    assert hacs["name"] == "RFLink Raw Tools"
    assert hacs["content_in_root"] is False
    assert "domains" not in hacs

    for key in ["domain", "name", "documentation", "issue_tracker", "codeowners", "version"]:
        assert manifest.get(key)

    assert manifest["domain"] == "rflink_raw"
    assert manifest["version"] == "0.0.1"

    assert (ROOT / ".github/workflows/hacs.yml").exists()
    assert (ROOT / ".github/workflows/hassfest.yml").exists()
    assert (ROOT / ".github/workflows/static-package.yml").exists()

def test_release_and_listing_docs_exist():
    assert (ROOT / "CHANGELOG.md").exists()
    assert (ROOT / "RELEASE_NOTES_v0.0.1.md").exists()
    checklist = (ROOT / "HACS_PUBLIC_LISTING_CHECKLIST.md").read_text()
    assert "home-assistant" in checklist
    assert "hacs-integration" in checklist
    assert "v0.0.1" in checklist

def test_package_has_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
