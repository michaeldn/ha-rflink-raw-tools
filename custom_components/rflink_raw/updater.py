"""Updater helpers for RFLink Raw Tools."""

from __future__ import annotations

import shutil
import tempfile
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Callable

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

REPO_ZIP_URL = "https://github.com/michaeldn/ha-rflink-raw-tools/archive/refs/heads/main.zip"

ProgressCallback = Callable[[int, str, str], None]


def _progress(callback: ProgressCallback | None, pct: int, status: str, message: str) -> None:
    if callback is not None:
        callback(pct, status, message)


def update_from_github(hass: HomeAssistant, progress_callback: ProgressCallback | None = None) -> str:
    """Update the integration files from GitHub with a backup first."""
    config_dir = Path(hass.config.path())
    target_dir = config_dir / "custom_components" / "rflink_raw"
    backup_root = config_dir / ".rflink_raw_backups"
    backup_dir = backup_root / f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_root.mkdir(parents=True, exist_ok=True)

    if not target_dir.exists():
        raise HomeAssistantError(f"Missing integration folder: {target_dir}")

    _progress(progress_callback, 10, "backing_up", "Backing up current RFLink Raw Tools files.")
    shutil.copytree(target_dir, backup_dir / "rflink_raw")

    with tempfile.TemporaryDirectory(prefix="rflink_raw_update_") as tmp:
        tmp_path = Path(tmp)
        zip_path = tmp_path / "repo.zip"
        extract_path = tmp_path / "extract"

        _progress(progress_callback, 25, "downloading", "Downloading latest package from GitHub.")
        urllib.request.urlretrieve(REPO_ZIP_URL, zip_path)

        _progress(progress_callback, 45, "extracting", "Extracting downloaded package.")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_path)

        repo_root = extract_path / "ha-rflink-raw-tools-main"
        new_component = repo_root / "custom_components" / "rflink_raw"
        if not new_component.exists():
            raise HomeAssistantError("Downloaded repo does not contain custom_components/rflink_raw.")

        _progress(progress_callback, 65, "installing", "Replacing integration files.")
        shutil.rmtree(target_dir)
        shutil.copytree(new_component, target_dir)

        _progress(progress_callback, 80, "copying_assets", "Copying dashboard, logo, and helper scripts.")
        logo = repo_root / "assets" / "logo.png"
        if logo.exists():
            www = config_dir / "www" / "rflink_raw"
            www.mkdir(parents=True, exist_ok=True)
            shutil.copy2(logo, www / "logo.png")

        dashboard = repo_root / "dashboard" / "rflink_raw_dashboard.yaml"
        if dashboard.exists():
            shutil.copy2(dashboard, config_dir / "rflink_raw_dashboard.yaml")

        for script_name in (
            "repair-stale-rflink-raw-entities.sh",
            "reset-rflink-raw-ui.sh",
            "fix-rflink-dashboard-mode.sh",
            "fix-rflink-brand-assets.sh",
            "rebuild-rflink-dashboard-note.sh",
            "undo-rflink-raw-tools.sh",
        ):
            script = repo_root / script_name
            if script.exists():
                target = config_dir / script_name
                shutil.copy2(script, target)
                target.chmod(0o755)

    _progress(progress_callback, 100, "complete", "Update installed. Restart Home Assistant Core.")
    return str(backup_dir)


def restore_last_update(
    hass: HomeAssistant,
    backup_path: str,
    progress_callback: ProgressCallback | None = None,
) -> str:
    """Restore the last integration backup."""
    if not backup_path:
        raise HomeAssistantError("No update backup is stored.")

    backup_dir = Path(backup_path)
    component_backup = backup_dir / "rflink_raw"
    if not component_backup.exists():
        raise HomeAssistantError(f"Backup does not exist: {component_backup}")

    _progress(progress_callback, 15, "restoring", "Restoring previous RFLink Raw Tools backup.")
    target_dir = Path(hass.config.path("custom_components/rflink_raw"))
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(component_backup, target_dir)
    _progress(progress_callback, 100, "restore_complete", "Backup restored. Restart Home Assistant Core.")

    return str(backup_dir)
