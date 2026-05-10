"""Managed configuration file changes for RFLink Raw Tools."""

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
    KEY_DASHBOARD_SHOW_IN_SIDEBAR,
    KEY_PREREQ_INSTALLED,
    MANAGED_BLOCK_END,
    MANAGED_BLOCK_START,
    MANAGED_DASHBOARD_BLOCK_END,
    MANAGED_DASHBOARD_BLOCK_START,
)
from .store import update_state
from .dashboard_builder import async_write_dashboard_file


def _backup_config(config_path: Path, label: str) -> Path:
    backup_path = config_path.with_name(
        f"configuration.yaml.rflink_raw_{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    shutil.copy2(config_path, backup_path)
    return backup_path


def _strip_block(text: str, start: str, end: str) -> str:
    return re.sub(rf"{re.escape(start)}.*?{re.escape(end)}\n?", "", text, flags=re.S)


def _has_unmanaged_top_level(text: str, key: str, start: str, end: str) -> bool:
    text_without_managed = _strip_block(text, start, end)
    return re.search(rf"(?m)^{re.escape(key)}:\s*$", text_without_managed) is not None


def install_prerequisite(
    hass: HomeAssistant,
    port: str,
    wait_for_ack: bool,
    reconnect_interval: int,
) -> Path:
    """Install/update the managed RFLink prerequisite block."""
    config_path = Path(hass.config.path("configuration.yaml"))
    text = config_path.read_text()

    if _has_unmanaged_top_level(text, "rflink", MANAGED_BLOCK_START, MANAGED_BLOCK_END):
        raise HomeAssistantError("configuration.yaml already has an unmanaged top-level rflink: block.")

    clean_port = (port or "").strip()
    if not clean_port:
        raise HomeAssistantError("RFLink port cannot be empty.")

    block = (
        f"{MANAGED_BLOCK_START}\n"
        "rflink:\n"
        f"  port: {clean_port}\n"
        f"  wait_for_ack: {'true' if wait_for_ack else 'false'}\n"
        f"  reconnect_interval: {int(reconnect_interval)}\n"
        f"{MANAGED_BLOCK_END}\n"
    )

    backup = _backup_config(config_path, "install_prerequisite")
    text = _strip_block(text, MANAGED_BLOCK_START, MANAGED_BLOCK_END)
    if text and not text.endswith("\n"):
        text += "\n"
    config_path.write_text(text + "\n" + block)
    update_state(hass, **{KEY_PREREQ_INSTALLED: True})
    return backup


def remove_prerequisite(hass: HomeAssistant) -> Path:
    """Remove only the managed RFLink prerequisite block."""
    config_path = Path(hass.config.path("configuration.yaml"))
    text = config_path.read_text()
    backup = _backup_config(config_path, "remove_prerequisite")
    config_path.write_text(_strip_block(text, MANAGED_BLOCK_START, MANAGED_BLOCK_END))
    update_state(hass, **{KEY_PREREQ_INSTALLED: False})
    return backup


def install_dashboard(hass: HomeAssistant, show_in_sidebar: bool) -> Path:
    """Install/update the managed dashboard block."""
    config_path = Path(hass.config.path("configuration.yaml"))
    text = config_path.read_text()

    if _has_unmanaged_top_level(text, "lovelace", MANAGED_DASHBOARD_BLOCK_START, MANAGED_DASHBOARD_BLOCK_END):
        raise HomeAssistantError("configuration.yaml already has an unmanaged top-level lovelace: block.")

    block = (
        f"{MANAGED_DASHBOARD_BLOCK_START}\n"
        "lovelace:\n"
        "  mode: storage\n"
        "  dashboards:\n"
        f"    {DASHBOARD_KEY}:\n"
        "      mode: yaml\n"
        f"      filename: {DASHBOARD_FILENAME}\n"
        f"      title: {DASHBOARD_TITLE}\n"
        f"      icon: {DASHBOARD_ICON}\n"
        f"      show_in_sidebar: {'true' if show_in_sidebar else 'false'}\n"
        "      require_admin: false\n"
        f"{MANAGED_DASHBOARD_BLOCK_END}\n"
    )

    backup = _backup_config(config_path, "install_dashboard")
    text = _strip_block(text, MANAGED_DASHBOARD_BLOCK_START, MANAGED_DASHBOARD_BLOCK_END)
    if text and not text.endswith("\n"):
        text += "\n"
    config_path.write_text(text + "\n" + block)
    update_state(hass, **{KEY_DASHBOARD_ENABLED: True, KEY_DASHBOARD_SHOW_IN_SIDEBAR: bool(show_in_sidebar)})
    hass.async_create_task(async_write_dashboard_file(hass))
    return backup


def remove_dashboard(hass: HomeAssistant) -> Path:
    """Remove only the managed dashboard block and related files."""
    config_path = Path(hass.config.path("configuration.yaml"))
    text = config_path.read_text()
    backup = _backup_config(config_path, "remove_dashboard")
    config_path.write_text(_strip_block(text, MANAGED_DASHBOARD_BLOCK_START, MANAGED_DASHBOARD_BLOCK_END))

    dashboard_file = Path(hass.config.path(DASHBOARD_FILENAME))
    if dashboard_file.exists():
        dashboard_file.unlink()

    logo_dir = Path(hass.config.path("www/rflink_raw"))
    if logo_dir.exists():
        shutil.rmtree(logo_dir)

    update_state(hass, **{KEY_DASHBOARD_ENABLED: False, KEY_DASHBOARD_SHOW_IN_SIDEBAR: False})
    return backup
