"""GitHub updater for RFLink Raw Tools."""

from __future__ import annotations

import shutil
import tempfile
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import KEY_UPDATE_STATUS
from .store import timestamped, update_state

REPO_ZIP_URL = "https://github.com/michaeldn/ha-rflink-raw-tools/archive/refs/heads/main.zip"


def update_from_github(hass: HomeAssistant) -> None:
    """Update RFLink Raw Tools from the GitHub main branch."""
    config_dir = Path(hass.config.path())
    target_dir = config_dir / "custom_components" / "rflink_raw"
    www_dir = config_dir / "www" / "rflink_raw"
    dashboard_file = config_dir / "rflink_raw_dashboard.yaml"
    backup_root = config_dir / ".rflink_raw_backups"
    backup_root.mkdir(parents=True, exist_ok=True)

    if not target_dir.exists():
        raise HomeAssistantError(f"Could not find installed integration folder at {target_dir}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / f"rflink_raw_{timestamp}"

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

        shutil.copytree(target_dir, backup_dir)
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
            )
        },
    )


def show_update_status(hass: HomeAssistant) -> None:
    """Store a simple update/status message."""
    config_dir = Path(hass.config.path())
    target_dir = config_dir / "custom_components" / "rflink_raw"
    update_state(
        hass,
        **{
            KEY_UPDATE_STATUS: timestamped(
                f"Installed folder: {target_dir}. Use Update Download Latest From GitHub, then restart Home Assistant Core."
            )
        },
    )
