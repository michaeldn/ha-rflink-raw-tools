"""Dashboard installer/remover for RFLink Raw Tools."""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DASHBOARD_FILENAME,
    DASHBOARD_ICON,
    DASHBOARD_KEY,
    DASHBOARD_TITLE,
    KEY_DASHBOARD_ENABLED,
    KEY_DASHBOARD_REQUIRE_ADMIN,
    KEY_DASHBOARD_SHOW_IN_SIDEBAR,
    KEY_DASHBOARD_STATUS,
    MANAGED_DASHBOARD_BLOCK_END,
    MANAGED_DASHBOARD_BLOCK_START,
)
from .store import timestamped, update_state


def _backup_config(config_path: Path, label: str) -> Path:
    backup_path = config_path.with_name(
        f"configuration.yaml.rflink_raw_{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    shutil.copy2(config_path, backup_path)
    return backup_path


def build_dashboard_yaml_block(show_in_sidebar: bool = True, require_admin: bool = False) -> str:
    """Build the managed YAML dashboard registration block."""
    show_value = "true" if show_in_sidebar else "false"
    admin_value = "true" if require_admin else "false"
    return (
        f"{MANAGED_DASHBOARD_BLOCK_START}\n"
        "lovelace:\n"
        "  resource_mode: storage\n"
        "  dashboards:\n"
        f"    {DASHBOARD_KEY}:\n"
        "      mode: yaml\n"
        f"      filename: {DASHBOARD_FILENAME}\n"
        f"      title: {DASHBOARD_TITLE}\n"
        f"      icon: {DASHBOARD_ICON}\n"
        f"      show_in_sidebar: {show_value}\n"
        f"      require_admin: {admin_value}\n"
        f"{MANAGED_DASHBOARD_BLOCK_END}\n"
    )


def _strip_managed_dashboard_block(text: str) -> str:
    return re.sub(
        rf"{re.escape(MANAGED_DASHBOARD_BLOCK_START)}.*?{re.escape(MANAGED_DASHBOARD_BLOCK_END)}\n?",
        "",
        text,
        flags=re.S,
    )


def _has_existing_unmanaged_lovelace(text: str) -> bool:
    text_without_managed = _strip_managed_dashboard_block(text)
    return re.search(r"(?m)^lovelace:\s*$", text_without_managed) is not None


def install_dashboard_registration(
    hass: HomeAssistant,
    show_in_sidebar: bool = True,
    require_admin: bool = False,
) -> Path:
    """Install/update the managed Lovelace dashboard registration block."""
    config_path = Path(hass.config.path("configuration.yaml"))
    if not config_path.exists():
        raise HomeAssistantError(f"Could not find configuration.yaml at {config_path}")

    text = config_path.read_text()

    if _has_existing_unmanaged_lovelace(text):
        msg = (
            "Existing unmanaged top-level lovelace: block found in configuration.yaml. "
            "RFLink Raw Tools will not create a duplicate. Add the dashboard manually "
            "under your existing lovelace.dashboards section."
        )
        update_state(hass, **{KEY_DASHBOARD_STATUS: timestamped(msg)})
        raise HomeAssistantError(msg)

    backup_path = _backup_config(config_path, "dashboard_install_backup")
    new_block = build_dashboard_yaml_block(show_in_sidebar, require_admin)

    if MANAGED_DASHBOARD_BLOCK_START in text and MANAGED_DASHBOARD_BLOCK_END in text:
        updated = re.sub(
            rf"{re.escape(MANAGED_DASHBOARD_BLOCK_START)}.*?{re.escape(MANAGED_DASHBOARD_BLOCK_END)}\n?",
            new_block,
            text,
            flags=re.S,
        )
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        updated = text + "\n" + new_block

    config_path.write_text(updated)

    msg = (
        f"Dashboard registered. show_in_sidebar={show_in_sidebar}, "
        f"require_admin={require_admin}. Run 'ha core check' and restart Home Assistant Core."
    )
    update_state(
        hass,
        **{
            KEY_DASHBOARD_STATUS: timestamped(msg),
            KEY_DASHBOARD_ENABLED: True,
            KEY_DASHBOARD_SHOW_IN_SIDEBAR: show_in_sidebar,
            KEY_DASHBOARD_REQUIRE_ADMIN: require_admin,
        },
    )
    return backup_path


def remove_dashboard_registration(hass: HomeAssistant, remove_files: bool = True) -> Path:
    """Remove only the managed dashboard registration block and optional dashboard files."""
    config_path = Path(hass.config.path("configuration.yaml"))
    if not config_path.exists():
        raise HomeAssistantError(f"Could not find configuration.yaml at {config_path}")

    text = config_path.read_text()
    backup_path = _backup_config(config_path, "dashboard_remove_backup")
    updated = _strip_managed_dashboard_block(text)
    config_path.write_text(updated)

    if remove_files:
        dashboard_file = Path(hass.config.path(DASHBOARD_FILENAME))
        if dashboard_file.exists():
            dashboard_file.unlink()
        logo_dir = Path(hass.config.path("www/rflink_raw"))
        if logo_dir.exists():
            shutil.rmtree(logo_dir)

    msg = "Managed dashboard registration removed. Run 'ha core check' and restart Home Assistant Core."
    update_state(
        hass,
        **{
            KEY_DASHBOARD_STATUS: timestamped(msg),
            KEY_DASHBOARD_ENABLED: False,
            KEY_DASHBOARD_SHOW_IN_SIDEBAR: False,
        },
    )
    return backup_path
