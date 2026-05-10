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

try:
    from .dashboard_builder import async_write_dashboard_file
except Exception:  # pragma: no cover
    async_write_dashboard_file = None


def _backup_config(config_path: Path, label: str) -> Path:
    backup_path = config_path.with_name(
        f"configuration.yaml.rflink_raw_{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    shutil.copy2(config_path, backup_path)
    return backup_path


def _strip_block(text: str, start: str, end: str) -> str:
    return re.sub(rf"{re.escape(start)}.*?{re.escape(end)}\n?", "", text, flags=re.S)


def _has_top_level(text: str, key: str) -> bool:
    return re.search(rf"(?m)^{re.escape(key)}:\s*$", text) is not None


def has_any_rflink_prerequisite(hass: HomeAssistant) -> bool:
    """Return true when any top-level RFLink config exists.

    The prerequisite is simply that the normal Home Assistant RFLink
    integration is configured. It can be user-managed or RFLink Raw
    Tools-managed.
    """
    config_path = Path(hass.config.path("configuration.yaml"))
    if not config_path.exists():
        return False
    text = config_path.read_text()
    return MANAGED_BLOCK_START in text or _has_top_level(text, "rflink")


def sync_prerequisite_state(hass: HomeAssistant) -> bool:
    """Sync the switch state from configuration.yaml."""
    satisfied = has_any_rflink_prerequisite(hass)
    update_state(hass, **{KEY_PREREQ_INSTALLED: satisfied})
    return satisfied


def _has_unmanaged_top_level(text: str, key: str, start: str, end: str) -> bool:
    text_without_managed = _strip_block(text, start, end)
    return _has_top_level(text_without_managed, key)


def install_prerequisite(
    hass: HomeAssistant,
    port: str,
    wait_for_ack: bool,
    reconnect_interval: int,
) -> Path | None:
    """Install/update the managed RFLink prerequisite block.

    If configuration.yaml already has any top-level rflink: block, the
    normal Home Assistant RFLink integration is already configured. In that
    case RFLink Raw Tools marks the prerequisite switch ON and does not write
    or duplicate YAML.
    """
    config_path = Path(hass.config.path("configuration.yaml"))
    text = config_path.read_text()

    # Existing user-managed RFLink config satisfies the prerequisite.
    if _has_unmanaged_top_level(text, "rflink", MANAGED_BLOCK_START, MANAGED_BLOCK_END):
        update_state(hass, **{KEY_PREREQ_INSTALLED: True})
        return None

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


def remove_prerequisite(hass: HomeAssistant) -> Path | None:
    """Remove only the managed RFLink prerequisite block.

    If RFLink is user-managed outside RFLink Raw Tools, turning this switch
    off should not remove or falsify the prerequisite. It remains ON because
    RFLink is still configured.
    """
    config_path = Path(hass.config.path("configuration.yaml"))
    text = config_path.read_text()

    if MANAGED_BLOCK_START not in text:
        # Nothing managed to undo. If the user has their own rflink block,
        # keep the switch true because the prerequisite is still satisfied.
        update_state(hass, **{KEY_PREREQ_INSTALLED: _has_top_level(text, "rflink")})
        return None

    backup = _backup_config(config_path, "remove_prerequisite")
    updated = _strip_block(text, MANAGED_BLOCK_START, MANAGED_BLOCK_END)
    config_path.write_text(updated)
    update_state(hass, **{KEY_PREREQ_INSTALLED: _has_top_level(updated, "rflink")})
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
    update_state(
        hass,
        **{
            KEY_DASHBOARD_ENABLED: True,
            KEY_DASHBOARD_SHOW_IN_SIDEBAR: bool(show_in_sidebar),
        },
    )
    if async_write_dashboard_file is not None:
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

    update_state(
        hass,
        **{
            KEY_DASHBOARD_ENABLED: False,
            KEY_DASHBOARD_SHOW_IN_SIDEBAR: False,
        },
    )
    return backup
