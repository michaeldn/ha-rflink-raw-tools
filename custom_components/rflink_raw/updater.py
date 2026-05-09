"""GitHub updater/restorer for RFLink Raw Tools."""

from __future__ import annotations

import shutil
import tempfile
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import KEY_UPDATE_BACKUP_PATH, KEY_UPDATE_STATUS
from .store import get_state, timestamped, update_state

REPO_ZIP_URL = "https://github.com/michaeldn/ha-rflink-raw-tools/archive/refs/heads/main.zip"


def _copy_optional(src: Path, dst: Path) -> None:
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    elif src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def update_from_github(hass: HomeAssistant) -> None:
    """Update RFLink Raw Tools from GitHub main with a restorable backup."""
    config_dir = Path(hass.config.path())
    target_dir = config_dir / "custom_components" / "rflink_raw"
    www_dir = config_dir / "www" / "rflink_raw"
    dashboard_file = config_dir / "rflink_raw_dashboard.yaml"
    backup_root = config_dir / ".rflink_raw_backups"
    backup_root.mkdir(parents=True, exist_ok=True)

    if not target_dir.exists():
        raise HomeAssistantError(f"Could not find installed integration folder at {target_dir}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / f"update_backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    shutil.copytree(target_dir, backup_dir / "rflink_raw")
    _copy_optional(www_dir, backup_dir / "www_rflink_raw")
    _copy_optional(dashboard_file, backup_dir / "rflink_raw_dashboard.yaml")

    with tempfile.TemporaryDirectory(prefix="rflink_raw_update_") as tmp:
        tmp_path = Path(tmp)
        zip_path = tmp_path / "ha-rflink-raw-tools.zip"
        extract_path = tmp_path / "extract"

        urllib.request.urlretrieve(REPO_ZIP_URL, zip_path)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_path)

        repo_dir = extract_path / "ha-rflink-raw-tools-main"
        new_component = repo_dir / "custom_components" / "rflink_raw"

        if not new_component.exists():
            raise HomeAssistantError(
                "Downloaded GitHub package did not contain custom_components/rflink_raw"
            )

        shutil.copytree(new_component, target_dir, dirs_exist_ok=True)

        logo_file = repo_dir / "assets" / "logo.png"
        if logo_file.exists():
            www_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(logo_file, www_dir / "logo.png")

        dashboard_source = repo_dir / "dashboard" / "rflink_raw_dashboard.yaml"
        if dashboard_source.exists():
            shutil.copy2(dashboard_source, dashboard_file)

    update_state(
        hass,
        **{
            KEY_UPDATE_STATUS: timestamped(
                "Updated from GitHub main. Restart Home Assistant Core to load the new version. "
                f"Backup saved to {backup_dir}"
            ),
            KEY_UPDATE_BACKUP_PATH: str(backup_dir),
        },
    )


def restore_last_update(hass: HomeAssistant) -> None:
    """Restore the last backup created by update_from_github()."""
    config_dir = Path(hass.config.path())
    state = get_state(hass)
    backup_path = state.get(KEY_UPDATE_BACKUP_PATH) or ""
    if not backup_path:
        raise HomeAssistantError("No RFLink Raw Tools update backup path is stored.")

    backup_dir = Path(backup_path)
    if not backup_dir.exists():
        raise HomeAssistantError(f"Stored update backup folder does not exist: {backup_dir}")

    component_backup = backup_dir / "rflink_raw"
    if not component_backup.exists():
        raise HomeAssistantError(f"Backup is missing rflink_raw folder: {component_backup}")

    target_dir = config_dir / "custom_components" / "rflink_raw"
    www_dir = config_dir / "www" / "rflink_raw"
    dashboard_file = config_dir / "rflink_raw_dashboard.yaml"

    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(component_backup, target_dir)

    logo_backup = backup_dir / "www_rflink_raw"
    if www_dir.exists():
        shutil.rmtree(www_dir)
    if logo_backup.exists():
        shutil.copytree(logo_backup, www_dir)

    dashboard_backup = backup_dir / "rflink_raw_dashboard.yaml"
    if dashboard_file.exists():
        dashboard_file.unlink()
    if dashboard_backup.exists():
        shutil.copy2(dashboard_backup, dashboard_file)

    update_state(
        hass,
        **{
            KEY_UPDATE_STATUS: timestamped(
                f"Restored RFLink Raw Tools from backup {backup_dir}. Restart Home Assistant Core."
            )
        },
    )
