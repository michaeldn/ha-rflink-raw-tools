"""RFLink prerequisite installer/remover for RFLink Raw Tools."""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    KEY_PREREQ_INSTALLED,
    KEY_PREREQ_STATUS,
    MANAGED_BLOCK_END,
    MANAGED_BLOCK_START,
)
from .store import timestamped, update_state


def _bool_yaml(value: bool) -> str:
    return "true" if value else "false"


def _backup_config(config_path: Path, label: str) -> Path:
    backup_path = config_path.with_name(
        f"configuration.yaml.rflink_raw_{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    shutil.copy2(config_path, backup_path)
    return backup_path


def build_rflink_yaml_block(port: str, wait_for_ack: bool, reconnect_interval: int) -> str:
    """Build the managed RFLink YAML prerequisite block."""
    clean_port = port.strip()
    if not clean_port:
        raise HomeAssistantError("RFLink port cannot be empty.")
    if "\n" in clean_port or "\r" in clean_port:
        raise HomeAssistantError("RFLink port must be one line.")
    if reconnect_interval < 1:
        raise HomeAssistantError("Reconnect interval must be at least 1 second.")

    return (
        f"{MANAGED_BLOCK_START}\n"
        "rflink:\n"
        f"  port: {clean_port}\n"
        f"  wait_for_ack: {_bool_yaml(wait_for_ack)}\n"
        f"  reconnect_interval: {int(reconnect_interval)}\n"
        f"{MANAGED_BLOCK_END}\n"
    )


def _strip_managed_rflink_block(text: str) -> str:
    return re.sub(
        rf"{re.escape(MANAGED_BLOCK_START)}.*?{re.escape(MANAGED_BLOCK_END)}\n?",
        "",
        text,
        flags=re.S,
    )


def _has_existing_unmanaged_rflink(text: str) -> bool:
    text_without_managed = _strip_managed_rflink_block(text)
    return re.search(r"(?m)^rflink:\s*$", text_without_managed) is not None


def install_rflink_prerequisite(
    hass: HomeAssistant,
    port: str,
    wait_for_ack: bool,
    reconnect_interval: int,
) -> Path:
    """Install/update the managed RFLink prerequisite block."""
    config_path = Path(hass.config.path("configuration.yaml"))
    if not config_path.exists():
        raise HomeAssistantError(f"Could not find configuration.yaml at {config_path}")

    text = config_path.read_text()
    new_block = build_rflink_yaml_block(port, wait_for_ack, reconnect_interval)

    if _has_existing_unmanaged_rflink(text):
        msg = (
            "Existing unmanaged top-level rflink: block found in configuration.yaml. "
            "RFLink Raw Tools will not create a duplicate. Edit the existing block manually "
            "or remove it before using the installer."
        )
        update_state(hass, **{KEY_PREREQ_STATUS: timestamped(msg)})
        raise HomeAssistantError(msg)

    backup_path = _backup_config(config_path, "prereq_install_backup")

    if MANAGED_BLOCK_START in text and MANAGED_BLOCK_END in text:
        updated = re.sub(
            rf"{re.escape(MANAGED_BLOCK_START)}.*?{re.escape(MANAGED_BLOCK_END)}\n?",
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
        "RFLink prerequisite YAML installed. "
        f"Port={port.strip()}, wait_for_ack={wait_for_ack}, reconnect_interval={int(reconnect_interval)}. "
        "Run 'ha core check' and restart Home Assistant Core."
    )
    update_state(hass, **{KEY_PREREQ_STATUS: timestamped(msg), KEY_PREREQ_INSTALLED: True})
    return backup_path


def remove_rflink_prerequisite(hass: HomeAssistant) -> Path:
    """Remove only the managed RFLink prerequisite block."""
    config_path = Path(hass.config.path("configuration.yaml"))
    if not config_path.exists():
        raise HomeAssistantError(f"Could not find configuration.yaml at {config_path}")

    text = config_path.read_text()
    backup_path = _backup_config(config_path, "prereq_remove_backup")
    updated = _strip_managed_rflink_block(text)
    config_path.write_text(updated)

    msg = "Managed RFLink prerequisite block removed. Run 'ha core check' and restart Home Assistant Core."
    update_state(hass, **{KEY_PREREQ_STATUS: timestamped(msg), KEY_PREREQ_INSTALLED: False})
    return backup_path
