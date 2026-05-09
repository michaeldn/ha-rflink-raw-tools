"""Button platform for RFLink Raw Tools."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components import persistent_notification
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription

from .const import (
    COMMAND_DEVICE_IDENTIFIER,
    COMMAND_DEVICE_NAME,
    DASHBOARD_URL,
    DEVICE_IDENTIFIER,
    DEVICE_NAME,
    DOMAIN,
    KEY_DELAY_MS,
    KEY_PROTOCOL_COMMAND,
    KEY_PROTOCOL_DEVICE_ID,
    KEY_RAW_COMMAND,
    KEY_REPEAT,
    MANUFACTURER,
    MODEL,
    VERSION,
)
from .helpers import async_send_direct_command, async_send_protocol_command
from .store import get_state
from .updater import restore_last_update, update_from_github


@dataclass(frozen=True, kw_only=True)
class RFLinkRawButtonDescription(EntityDescription):
    """Description for an RFLink raw tools button."""

    command: str | None = None
    action_type: str = "direct"
    entity_category: str | None = None
    enabled_default: bool = True
    device_area: str = "command"


BUTTONS: tuple[RFLinkRawButtonDescription, ...] = (
    RFLinkRawButtonDescription(
        key="open_dashboard",
        name="Show Dashboard Path",
        icon="mdi:information-outline",
        action_type="open_dashboard",
        entity_category="diagnostic",
        enabled_default=False,
        device_area="admin",
    ),
    RFLinkRawButtonDescription(
        key="update_download_latest",
        name="Update Download Latest From GitHub",
        icon="mdi:cloud-download-outline",
        action_type="update_from_github",
        entity_category="config",
        enabled_default=True,
        device_area="admin",
    ),
    RFLinkRawButtonDescription(
        key="restore_last_update",
        name="Undo Last GitHub Update",
        icon="mdi:backup-restore",
        action_type="restore_last_update",
        entity_category="config",
        enabled_default=True,
        device_area="admin",
    ),
    RFLinkRawButtonDescription(
        key="control_send_raw_text",
        name="Control Send RFLink Raw Command",
        icon="mdi:send",
        action_type="send_raw_text",
    ),
    RFLinkRawButtonDescription(
        key="control_send_protocol_text",
        name="Control Send RFLink Protocol Command",
        icon="mdi:remote",
        action_type="send_protocol_text",
    ),
    RFLinkRawButtonDescription(
        key="debug_ping",
        name="Debug RFLink Ping",
        icon="mdi:access-point-check",
        command="10;PING;",
        entity_category="config",
    ),
    RFLinkRawButtonDescription(
        key="debug_version",
        name="Debug RFLink Version",
        icon="mdi:information-outline",
        command="10;VERSION;",
        entity_category="config",
    ),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up RFLink Raw Tools buttons."""
    async_add_entities(RFLinkRawButton(hass, entry.entry_id, description) for description in BUTTONS)


class RFLinkRawButton(ButtonEntity):
    """RFLink command button."""

    _attr_has_entity_name = False

    def __init__(self, hass, entry_id: str, description: RFLinkRawButtonDescription) -> None:
        self.hass = hass
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = description.enabled_default

        if description.device_area == "admin":
            identifier = DEVICE_IDENTIFIER
            name = DEVICE_NAME
        else:
            identifier = COMMAND_DEVICE_IDENTIFIER
            name = COMMAND_DEVICE_NAME

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=VERSION,
        )

    async def async_press(self) -> None:
        state = get_state(self.hass)

        if self.entity_description.action_type == "open_dashboard":
            persistent_notification.async_create(
                self.hass,
                f"Open **RFLink Raw Tools** from the left sidebar if enabled. Direct path: `{DASHBOARD_URL}`",
                title="RFLink Raw Tools • Open Dashboard",
                notification_id="rflink_raw_open_dashboard",
            )
            return

        if self.entity_description.action_type == "update_from_github":
            update_from_github(self.hass)
            persistent_notification.async_create(
                self.hass,
                "RFLink Raw Tools was updated from GitHub. Restart Home Assistant Core. "
                "Use **Undo Last GitHub Update** before restarting if needed.",
                title="RFLink Raw Tools • Update Downloaded",
                notification_id="rflink_raw_update_done",
            )
            return

        if self.entity_description.action_type == "restore_last_update":
            restore_last_update(self.hass)
            persistent_notification.async_create(
                self.hass,
                "RFLink Raw Tools restored the last update backup. Restart Home Assistant Core.",
                title="RFLink Raw Tools • Update Restored",
                notification_id="rflink_raw_update_restored",
            )
            return

        if self.entity_description.action_type == "send_raw_text":
            await async_send_direct_command(
                self.hass,
                state[KEY_RAW_COMMAND],
                state[KEY_REPEAT],
                state[KEY_DELAY_MS],
            )
            return

        if self.entity_description.action_type == "send_protocol_text":
            await async_send_protocol_command(
                self.hass,
                state[KEY_PROTOCOL_DEVICE_ID],
                state[KEY_PROTOCOL_COMMAND],
                state[KEY_REPEAT],
                state[KEY_DELAY_MS],
            )
            return

        await async_send_direct_command(self.hass, self.entity_description.command, 1, 250)
