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
    KEY_DASHBOARD_REQUIRE_ADMIN,
    KEY_DASHBOARD_SHOW_IN_SIDEBAR,
    KEY_DELAY_MS,
    KEY_PREREQ_PORT,
    KEY_PREREQ_RECONNECT_INTERVAL,
    KEY_PREREQ_WAIT_FOR_ACK,
    KEY_PROTOCOL_COMMAND,
    KEY_PROTOCOL_DEVICE_ID,
    KEY_RAW_COMMAND,
    KEY_REPEAT,
    MANUFACTURER,
    MODEL,
    VERSION,
)
from .dashboard import install_dashboard_registration
from .helpers import async_send_direct_command, async_send_protocol_command
from .prereq import install_rflink_prerequisite
from .store import get_state, update_state
from .updater import show_update_status, update_from_github


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
        name="Open RFLink Tools Dashboard",
        icon="mdi:open-in-new",
        action_type="open_dashboard",
        device_area="admin",
    ),
    RFLinkRawButtonDescription(
        key="add_dashboard",
        name="Add Dashboard",
        icon="mdi:view-dashboard-plus-outline",
        action_type="add_dashboard",
        device_area="admin",
    ),
    RFLinkRawButtonDescription(
        key="add_to_sidebar",
        name="Add To Sidebar",
        icon="mdi:menu-open",
        action_type="add_to_sidebar",
        device_area="admin",
    ),
    RFLinkRawButtonDescription(
        key="update_download_latest",
        name="Update Download Latest From GitHub",
        icon="mdi:cloud-download-outline",
        action_type="update_from_github",
        entity_category="config",
        enabled_default=False,
        device_area="admin",
    ),
    RFLinkRawButtonDescription(
        key="setup_install_prerequisite",
        name="Setup Install RFLink Prerequisite YAML",
        icon="mdi:file-cog-outline",
        action_type="install_prerequisite",
        entity_category="config",
        enabled_default=False,
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
        key="help_load_example_raw",
        name="Help Load Example Raw Command",
        icon="mdi:code-tags",
        action_type="load_example_raw",
        entity_category="diagnostic",
        enabled_default=False,
    ),
    RFLinkRawButtonDescription(
        key="help_load_example_protocol",
        name="Help Load Example Protocol Command",
        icon="mdi:gesture-tap-button",
        action_type="load_example_protocol",
        entity_category="diagnostic",
        enabled_default=False,
    ),
    RFLinkRawButtonDescription(key="debug_ping", name="Debug RFLink Ping", icon="mdi:access-point-check", command="10;PING;", entity_category="config"),
    RFLinkRawButtonDescription(key="debug_version", name="Debug RFLink Version", icon="mdi:information-outline", command="10;VERSION;", entity_category="config"),
    RFLinkRawButtonDescription(key="debug_qrfdebug_on", name="Debug Start QRFDEBUG Capture", icon="mdi:signal", command="10;QRFDEBUG=ON;", entity_category="config"),
    RFLinkRawButtonDescription(key="debug_qrfdebug_off", name="Debug Stop QRFDEBUG Capture", icon="mdi:signal-off", command="10;QRFDEBUG=OFF;", entity_category="config"),
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
                f"Open the **RFLink Raw Tools** item in the left sidebar. Direct path: `{DASHBOARD_URL}`",
                title="RFLink Raw Tools • Open Dashboard",
                notification_id="rflink_raw_open_dashboard",
            )
            return

        if self.entity_description.action_type == "add_dashboard":
            install_dashboard_registration(self.hass, False, False)
            persistent_notification.async_create(
                self.hass,
                "Dashboard registered. To also put it in the left menu, press **Add To Sidebar**, then restart Home Assistant Core.",
                title="RFLink Raw Tools • Dashboard Added",
                notification_id="rflink_raw_dashboard_added",
            )
            return

        if self.entity_description.action_type == "add_to_sidebar":
            update_state(self.hass, **{KEY_DASHBOARD_SHOW_IN_SIDEBAR: True, KEY_DASHBOARD_REQUIRE_ADMIN: False})
            install_dashboard_registration(self.hass, True, False)
            persistent_notification.async_create(
                self.hass,
                "Dashboard registered with sidebar enabled. Run `ha core check`, restart Home Assistant Core, then use **RFLink Raw Tools** in the left sidebar.",
                title="RFLink Raw Tools • Added To Sidebar",
                notification_id="rflink_raw_sidebar_added",
            )
            return

        if self.entity_description.action_type == "update_from_github":
            update_from_github(self.hass)
            persistent_notification.async_create(
                self.hass,
                "RFLink Raw Tools was updated from GitHub. Restart Home Assistant Core.",
                title="RFLink Raw Tools • Update Downloaded",
                notification_id="rflink_raw_update_done",
            )
            return

        if self.entity_description.action_type == "install_prerequisite":
            install_rflink_prerequisite(
                self.hass,
                state[KEY_PREREQ_PORT],
                bool(state[KEY_PREREQ_WAIT_FOR_ACK]),
                int(state[KEY_PREREQ_RECONNECT_INTERVAL]),
            )
            persistent_notification.async_create(
                self.hass,
                "RFLink prerequisite YAML was written. Run `ha core check` and restart.",
                title="RFLink Raw Tools • Prerequisite Installed",
                notification_id="rflink_raw_prereq_done",
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

        if self.entity_description.action_type == "load_example_raw":
            update_state(self.hass, **{KEY_RAW_COMMAND: "10;NewKaku;0cac142;3;ON;", KEY_REPEAT: 3, KEY_DELAY_MS: 250})
            return

        if self.entity_description.action_type == "load_example_protocol":
            update_state(self.hass, **{KEY_PROTOCOL_DEVICE_ID: "newkaku_0cac142_3", KEY_PROTOCOL_COMMAND: "on", KEY_REPEAT: 3, KEY_DELAY_MS: 250})
            return

        await async_send_direct_command(self.hass, self.entity_description.command, 1, 250)
