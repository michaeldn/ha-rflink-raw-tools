"""Switch platform for RFLink Raw Tools."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components import persistent_notification
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription

from .const import (
    COMMAND_DEVICE_IDENTIFIER,
    COMMAND_DEVICE_NAME,
    DEVICE_IDENTIFIER,
    DEVICE_NAME,
    DOMAIN,
    KEY_DASHBOARD_ENABLED,
    KEY_DASHBOARD_REQUIRE_ADMIN,
    KEY_DASHBOARD_SHOW_IN_SIDEBAR,
    KEY_PREREQ_INSTALLED,
    KEY_PREREQ_PORT,
    KEY_PREREQ_RECONNECT_INTERVAL,
    KEY_PREREQ_WAIT_FOR_ACK,
    MANUFACTURER,
    MODEL,
    VERSION,
)
from .dashboard import install_dashboard_registration, remove_dashboard_registration
from .helpers import async_send_direct_command
from .prereq import install_rflink_prerequisite, remove_rflink_prerequisite
from .store import get_state, update_state


@dataclass(frozen=True, kw_only=True)
class RFLinkRawSwitchDescription(EntityDescription):
    """Description for an RFLink Raw Tools switch."""

    state_key: str | None = None
    switch_type: str = "state"
    on_command: str | None = None
    off_command: str | None = None
    entity_category: str | None = None
    enabled_default: bool = True
    device_area: str = "admin"


SWITCHES: tuple[RFLinkRawSwitchDescription, ...] = (
    RFLinkRawSwitchDescription(
        key="admin_install_prerequisite",
        name="Install RFLink Prerequisite",
        icon="mdi:file-cog-outline",
        state_key=KEY_PREREQ_INSTALLED,
        switch_type="install_prereq",
        entity_category="config",
    ),
    RFLinkRawSwitchDescription(
        key="dashboard_enabled",
        name="Add Dashboard",
        icon="mdi:view-dashboard-plus-outline",
        state_key=KEY_DASHBOARD_ENABLED,
        switch_type="dashboard_enabled",
        entity_category="config",
    ),
    RFLinkRawSwitchDescription(
        key="dashboard_show_in_sidebar",
        name="Add To Sidebar",
        icon="mdi:menu-open",
        state_key=KEY_DASHBOARD_SHOW_IN_SIDEBAR,
        switch_type="dashboard_sidebar",
        entity_category="config",
    ),
    RFLinkRawSwitchDescription(
        key="dashboard_require_admin",
        name="Dashboard Require Admin",
        icon="mdi:shield-account-outline",
        state_key=KEY_DASHBOARD_REQUIRE_ADMIN,
        switch_type="dashboard_admin",
        entity_category="config",
        enabled_default=False,
    ),
    RFLinkRawSwitchDescription(
        key="setup_prereq_wait_for_ack",
        name="RFLink Prerequisite Wait For ACK",
        icon="mdi:handshake-outline",
        state_key=KEY_PREREQ_WAIT_FOR_ACK,
        switch_type="state",
        entity_category="config",
    ),
    RFLinkRawSwitchDescription(
        key="debug_rfdebug",
        name="Debug RFLink RFDEBUG",
        icon="mdi:radio-tower",
        switch_type="command",
        on_command="10;RFDEBUG=ON;",
        off_command="10;RFDEBUG=OFF;",
        entity_category="config",
        device_area="command",
    ),
    RFLinkRawSwitchDescription(
        key="debug_qrfdebug",
        name="Debug RFLink QRFDEBUG",
        icon="mdi:signal",
        switch_type="command",
        on_command="10;QRFDEBUG=ON;",
        off_command="10;QRFDEBUG=OFF;",
        entity_category="config",
        device_area="command",
    ),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up RFLink Raw Tools switches."""
    async_add_entities(RFLinkRawSwitch(hass, entry.entry_id, description) for description in SWITCHES)


class RFLinkRawSwitch(SwitchEntity):
    """RFLink Raw Tools switch."""

    _attr_has_entity_name = False

    def __init__(self, hass, entry_id: str, description: RFLinkRawSwitchDescription) -> None:
        self.hass = hass
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = description.enabled_default
        self._attr_is_on = False

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

    @property
    def is_on(self) -> bool:
        """Return switch state."""
        if self.entity_description.switch_type == "command":
            return bool(self._attr_is_on)
        return bool(get_state(self.hass).get(self.entity_description.state_key, False))

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on."""
        state = get_state(self.hass)

        if self.entity_description.switch_type == "install_prereq":
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

        elif self.entity_description.switch_type == "dashboard_enabled":
            install_dashboard_registration(
                self.hass,
                bool(state.get(KEY_DASHBOARD_SHOW_IN_SIDEBAR, False)),
                bool(state.get(KEY_DASHBOARD_REQUIRE_ADMIN, False)),
            )

        elif self.entity_description.switch_type == "dashboard_sidebar":
            update_state(self.hass, **{KEY_DASHBOARD_SHOW_IN_SIDEBAR: True, KEY_DASHBOARD_ENABLED: True})
            install_dashboard_registration(
                self.hass,
                True,
                bool(state.get(KEY_DASHBOARD_REQUIRE_ADMIN, False)),
            )

        elif self.entity_description.switch_type == "dashboard_admin":
            update_state(self.hass, **{KEY_DASHBOARD_REQUIRE_ADMIN: True})
            install_dashboard_registration(
                self.hass,
                bool(state.get(KEY_DASHBOARD_SHOW_IN_SIDEBAR, False)),
                True,
            )

        elif self.entity_description.switch_type == "command":
            await async_send_direct_command(self.hass, self.entity_description.on_command, 1, 250)
            self._attr_is_on = True

        else:
            update_state(self.hass, **{self.entity_description.state_key: True})

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off / undo."""
        state = get_state(self.hass)

        if self.entity_description.switch_type == "install_prereq":
            remove_rflink_prerequisite(self.hass)
            persistent_notification.async_create(
                self.hass,
                "Managed RFLink prerequisite block was removed. Run `ha core check` and restart.",
                title="RFLink Raw Tools • Prerequisite Removed",
                notification_id="rflink_raw_prereq_removed",
            )

        elif self.entity_description.switch_type == "dashboard_enabled":
            remove_dashboard_registration(self.hass, remove_files=True)

        elif self.entity_description.switch_type == "dashboard_sidebar":
            update_state(self.hass, **{KEY_DASHBOARD_SHOW_IN_SIDEBAR: False})
            install_dashboard_registration(
                self.hass,
                False,
                bool(state.get(KEY_DASHBOARD_REQUIRE_ADMIN, False)),
            )

        elif self.entity_description.switch_type == "dashboard_admin":
            update_state(self.hass, **{KEY_DASHBOARD_REQUIRE_ADMIN: False})
            install_dashboard_registration(
                self.hass,
                bool(state.get(KEY_DASHBOARD_SHOW_IN_SIDEBAR, False)),
                False,
            )

        elif self.entity_description.switch_type == "command":
            await async_send_direct_command(self.hass, self.entity_description.off_command, 1, 250)
            self._attr_is_on = False

        else:
            update_state(self.hass, **{self.entity_description.state_key: False})

        self.async_write_ha_state()
