"""Button entities for RFLink Raw Tools."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityDescription

from .const import (
    ADMIN_DEVICE_IDENTIFIER,
    ADMIN_DEVICE_NAME,
    COMMAND_DEVICE_IDENTIFIER,
    COMMAND_DEVICE_NAME,
    DOMAIN,
    KEY_DASHBOARD_ENABLED,
    KEY_DASHBOARD_SHOW_IN_SIDEBAR,
    KEY_DELAY_MS,
    KEY_PREREQ_INSTALLED,
    KEY_PREREQ_PORT,
    KEY_PREREQ_RECONNECT_INTERVAL,
    KEY_PREREQ_WAIT_FOR_ACK,
    KEY_PROTOCOL_COMMAND,
    KEY_PROTOCOL_DEVICE_ID,
    KEY_RAW_COMMAND,
    KEY_REPEAT,
    MANUFACTURER,
    MODEL,
    SIGNAL_STATE_UPDATED,
    VERSION,
)
from .helpers import async_send_direct_command, async_send_protocol_command
from .managed_config import install_dashboard, install_prerequisite, remove_dashboard, remove_prerequisite
from .store import get_state
from .updater import restore_last_update, update_from_github


@dataclass(frozen=True, kw_only=True)
class RFLinkRawButtonDescription(EntityDescription):
    """Button description."""

    action_type: str
    device_area: str = "admin"
    available_when_key: str | None = None
    available_when_value: bool | None = None
    command: str | None = None
    entity_category: str | None = None
    enabled_default: bool = True


BUTTONS = (
    RFLinkRawButtonDescription(
        key="install_prerequisite",
        name="Install RFLink Prerequisite",
        icon="mdi:file-cog-outline",
        action_type="install_prerequisite",
        available_when_key=KEY_PREREQ_INSTALLED,
        available_when_value=False,
    ),
    RFLinkRawButtonDescription(
        key="remove_prerequisite",
        name="Undo RFLink Prerequisite",
        icon="mdi:file-remove-outline",
        action_type="remove_prerequisite",
        available_when_key=KEY_PREREQ_INSTALLED,
        available_when_value=True,
    ),
    RFLinkRawButtonDescription(
        key="add_dashboard",
        name="Add Dashboard",
        icon="mdi:view-dashboard-plus-outline",
        action_type="add_dashboard",
        available_when_key=KEY_DASHBOARD_ENABLED,
        available_when_value=False,
    ),
    RFLinkRawButtonDescription(
        key="remove_dashboard",
        name="Undo Dashboard",
        icon="mdi:view-dashboard-remove-outline",
        action_type="remove_dashboard",
        available_when_key=KEY_DASHBOARD_ENABLED,
        available_when_value=True,
    ),
    RFLinkRawButtonDescription(
        key="add_to_sidebar",
        name="Add To Sidebar",
        icon="mdi:menu-open",
        action_type="add_to_sidebar",
        available_when_key=KEY_DASHBOARD_SHOW_IN_SIDEBAR,
        available_when_value=False,
    ),
    RFLinkRawButtonDescription(
        key="remove_from_sidebar",
        name="Remove From Sidebar",
        icon="mdi:menu",
        action_type="remove_from_sidebar",
        available_when_key=KEY_DASHBOARD_SHOW_IN_SIDEBAR,
        available_when_value=True,
    ),
    RFLinkRawButtonDescription(
        key="control_send_raw",
        name="Send RFLink Raw Command",
        icon="mdi:send",
        action_type="send_raw",
        device_area="command",
    ),
    RFLinkRawButtonDescription(
        key="control_send_protocol",
        name="Send RFLink Protocol Command",
        icon="mdi:remote",
        action_type="send_protocol",
        device_area="command",
    ),
    RFLinkRawButtonDescription(
        key="debug_ping",
        name="RFLink Ping",
        icon="mdi:access-point-check",
        action_type="direct",
        command="10;PING;",
        device_area="command",
    ),
    RFLinkRawButtonDescription(
        key="debug_version",
        name="RFLink Version",
        icon="mdi:information-outline",
        action_type="direct",
        command="10;VERSION;",
        device_area="command",
    ),
    RFLinkRawButtonDescription(
        key="update_from_github",
        name="Download Latest From GitHub",
        icon="mdi:cloud-download-outline",
        action_type="update_from_github",
        entity_category="config",
        enabled_default=False,
    ),
    RFLinkRawButtonDescription(
        key="restore_last_update",
        name="Undo Last GitHub Update",
        icon="mdi:backup-restore",
        action_type="restore_last_update",
        entity_category="config",
        enabled_default=False,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up button entities."""
    async_add_entities(RFLinkRawButton(hass, entry.entry_id, desc) for desc in BUTTONS)


class RFLinkRawButton(ButtonEntity):
    """RFLink Raw Tools button."""

    _attr_has_entity_name = False

    def __init__(self, hass, entry_id: str, description: RFLinkRawButtonDescription) -> None:
        self.hass = hass
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = description.enabled_default

        if description.device_area == "admin":
            identifier = ADMIN_DEVICE_IDENTIFIER
            name = ADMIN_DEVICE_NAME
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

    async def async_added_to_hass(self) -> None:
        """Refresh availability when state changes."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_STATE_UPDATED, self.async_write_ha_state)
        )

    @property
    def available(self) -> bool:
        """Return whether the button is currently available."""
        key = self.entity_description.available_when_key
        expected = self.entity_description.available_when_value
        if key is None:
            return True
        return bool(get_state(self.hass).get(key, False)) is bool(expected)

    async def async_press(self) -> None:
        """Press the button."""
        state = get_state(self.hass)
        action = self.entity_description.action_type

        if action == "install_prerequisite":
            install_prerequisite(
                self.hass,
                state[KEY_PREREQ_PORT],
                bool(state[KEY_PREREQ_WAIT_FOR_ACK]),
                int(state[KEY_PREREQ_RECONNECT_INTERVAL]),
            )
            return

        if action == "remove_prerequisite":
            remove_prerequisite(self.hass)
            return

        if action == "add_dashboard":
            install_dashboard(self.hass, bool(state.get(KEY_DASHBOARD_SHOW_IN_SIDEBAR, False)))
            return

        if action == "remove_dashboard":
            remove_dashboard(self.hass)
            return

        if action == "add_to_sidebar":
            install_dashboard(self.hass, True)
            return

        if action == "remove_from_sidebar":
            install_dashboard(self.hass, False)
            return

        if action == "send_raw":
            await async_send_direct_command(self.hass, state[KEY_RAW_COMMAND], state[KEY_REPEAT], state[KEY_DELAY_MS])
            return

        if action == "send_protocol":
            await async_send_protocol_command(
                self.hass,
                state[KEY_PROTOCOL_DEVICE_ID],
                state[KEY_PROTOCOL_COMMAND],
                state[KEY_REPEAT],
                state[KEY_DELAY_MS],
            )
            return

        if action == "update_from_github":
            update_from_github(self.hass)
            return

        if action == "restore_last_update":
            restore_last_update(self.hass)
            return

        if action == "direct":
            await async_send_direct_command(self.hass, self.entity_description.command, 1, 250)
