"""Updater helpers for RFLink Raw Tools."""

from __future__ import annotations

import shutil
import tempfile
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import KEY_LAST_UPDATE_BACKUP
from .store import get_state, update_state

REPO_ZIP_URL = "https://github.com/michaeldn/ha-rflink-raw-tools/archive/refs/heads/main.zip"


def update_from_github(hass: HomeAssistant) -> None:
    """Update the integration files from GitHub with a backup first."""
    config_dir = Path(hass.config.path())
    target_dir = config_dir / "custom_components" / "rflink_raw"
    backup_root = config_dir / ".rflink_raw_backups"
    backup_dir = backup_root / f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_root.mkdir(parents=True, exist_ok=True)

    if not target_dir.exists():
        raise HomeAssistantError(f"Missing integration folder: {target_dir}")

    shutil.copytree(target_dir, backup_dir / "rflink_raw")

    with tempfile.TemporaryDirectory(prefix="rflink_raw_update_") as tmp:
        tmp_path = Path(tmp)
        zip_path = tmp_path / "repo.zip"
        extract_path = tmp_path / "extract"

        urllib.request.urlretrieve(REPO_ZIP_URL, zip_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_path)

        repo_root = extract_path / "ha-rflink-raw-tools-main"
        new_component = repo_root / "custom_components" / "rflink_raw"
        if not new_component.exists():
            raise HomeAssistantError("Downloaded repo does not contain custom_components/rflink_raw.")

        shutil.rmtree(target_dir)
        shutil.copytree(new_component, target_dir)

        logo = repo_root / "assets" / "logo.png"
        if logo.exists():
            www = config_dir / "www" / "rflink_raw"
            www.mkdir(parents=True, exist_ok=True)
            shutil.copy2(logo, www / "logo.png")

        dashboard = repo_root / "dashboard" / "rflink_raw_dashboard.yaml"
        if dashboard.exists():
            shutil.copy2(dashboard, config_dir / "rflink_raw_dashboard.yaml")

    update_state(hass, **{KEY_LAST_UPDATE_BACKUP: str(backup_dir)})


def restore_last_update(hass: HomeAssistant) -> None:
    """Restore the last integration backup created by update_from_github."""
    state = get_state(hass)
    backup_path = state.get(KEY_LAST_UPDATE_BACKUP)
    if not backup_path:
        raise HomeAssistantError("No update backup is stored.")

    backup_dir = Path(backup_path)
    component_backup = backup_dir / "rflink_raw"
    if not component_backup.exists():
        raise HomeAssistantError(f"Backup does not exist: {component_backup}")

    target_dir = Path(hass.config.path("custom_components/rflink_raw"))
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(component_backup, target_dir)
