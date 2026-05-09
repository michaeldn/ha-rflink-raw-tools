"""Switch entities for RFLink Raw Tools."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity
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
    KEY_PREREQ_INSTALLED,
    KEY_PREREQ_PORT,
    KEY_PREREQ_RECONNECT_INTERVAL,
    KEY_PREREQ_WAIT_FOR_ACK,
    KEY_DELAY_MS,
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
from .store import get_state, update_state
from .updater import restore_last_update, update_from_github


@dataclass(frozen=True, kw_only=True)
class RFLinkRawSwitchDescription(EntityDescription):
    """Switch description."""

    switch_type: str
    device_area: str = "admin"
    state_key: str | None = None
    on_command: str | None = None
    off_command: str | None = None
    entity_category: str | None = None
    enabled_default: bool = True


SWITCHES: tuple[RFLinkRawSwitchDescription, ...] = (
    RFLinkRawSwitchDescription(
        key="managed_prerequisite",
        name="RFLink Prerequisite",
        icon="mdi:file-cog-outline",
        switch_type="managed_prerequisite",
        state_key=KEY_PREREQ_INSTALLED,
    ),
    RFLinkRawSwitchDescription(
        key="managed_dashboard",
        name="RFLink Dashboard",
        icon="mdi:view-dashboard-outline",
        switch_type="managed_dashboard",
        state_key=KEY_DASHBOARD_ENABLED,
    ),
    RFLinkRawSwitchDescription(
        key="managed_sidebar",
        name="RFLink Sidebar",
        icon="mdi:menu-open",
        switch_type="managed_sidebar",
        state_key=KEY_DASHBOARD_SHOW_IN_SIDEBAR,
    ),
    RFLinkRawSwitchDescription(
        key="prereq_wait_for_ack",
        name="RFLink Prerequisite Wait For ACK",
        icon="mdi:handshake-outline",
        switch_type="state",
        state_key=KEY_PREREQ_WAIT_FOR_ACK,
    ),
    RFLinkRawSwitchDescription(
        key="send_raw_command",
        name="Send RFLink Raw Command",
        icon="mdi:send",
        switch_type="momentary_send_raw",
        device_area="command",
    ),
    RFLinkRawSwitchDescription(
        key="send_protocol_command",
        name="Send RFLink Protocol Command",
        icon="mdi:remote",
        switch_type="momentary_send_protocol",
        device_area="command",
    ),
    RFLinkRawSwitchDescription(
        key="qrfdebug",
        name="RFLink QRFDEBUG",
        icon="mdi:signal",
        switch_type="command",
        on_command="10;QRFDEBUG=ON;",
        off_command="10;QRFDEBUG=OFF;",
        device_area="command",
    ),
    RFLinkRawSwitchDescription(
        key="rfdebug",
        name="RFLink RFDEBUG",
        icon="mdi:radio-tower",
        switch_type="command",
        on_command="10;RFDEBUG=ON;",
        off_command="10;RFDEBUG=OFF;",
        device_area="command",
    ),
    RFLinkRawSwitchDescription(
        key="ping",
        name="RFLink Ping",
        icon="mdi:access-point-check",
        switch_type="momentary_direct",
        on_command="10;PING;",
        device_area="command",
    ),
    RFLinkRawSwitchDescription(
        key="version",
        name="RFLink Version",
        icon="mdi:information-outline",
        switch_type="momentary_direct",
        on_command="10;VERSION;",
        device_area="command",
    ),
    RFLinkRawSwitchDescription(
        key="update_from_github",
        name="Update Download Latest From GitHub",
        icon="mdi:cloud-download-outline",
        switch_type="momentary_update",
        entity_category="config",
        enabled_default=False,
    ),
    RFLinkRawSwitchDescription(
        key="restore_last_update",
        name="Undo Last GitHub Update",
        icon="mdi:backup-restore",
        switch_type="momentary_restore",
        entity_category="config",
        enabled_default=False,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up switch entities."""
    async_add_entities(RFLinkRawSwitch(hass, entry.entry_id, description) for description in SWITCHES)


class RFLinkRawSwitch(SwitchEntity):
    """RFLink Raw Tools switch.

    There are no ButtonEntity objects in this build because Home Assistant's native
    device page renders ButtonEntity actions as "Press".
    """

    _attr_has_entity_name = False

    def __init__(self, hass, entry_id: str, description: RFLinkRawSwitchDescription) -> None:
        self.hass = hass
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = description.enabled_default
        self._command_is_on = False
        self._momentary_is_on = False

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
        """Refresh state when stored state changes."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_STATE_UPDATED, self.async_write_ha_state)
        )

    @property
    def is_on(self) -> bool:
        """Return switch state."""
        switch_type = self.entity_description.switch_type
        if switch_type in {"state", "managed_prerequisite", "managed_dashboard", "managed_sidebar"}:
            return bool(get_state(self.hass).get(self.entity_description.state_key, False))
        if switch_type.startswith("momentary_"):
            return bool(self._momentary_is_on)
        return bool(self._command_is_on)

    async def _momentary_done(self) -> None:
        """Reset momentary switch back off."""
        await asyncio.sleep(0.5)
        self._momentary_is_on = False
        self.async_write_ha_state()

    async def _run_momentary(self, coro_or_fn) -> None:
        self._momentary_is_on = True
        self.async_write_ha_state()
        result = coro_or_fn()
        if hasattr(result, "__await__"):
            await result
        self.hass.async_create_task(self._momentary_done())

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on."""
        state = get_state(self.hass)
        switch_type = self.entity_description.switch_type

        if switch_type == "managed_prerequisite":
            install_prerequisite(
                self.hass,
                state[KEY_PREREQ_PORT],
                bool(state[KEY_PREREQ_WAIT_FOR_ACK]),
                int(state[KEY_PREREQ_RECONNECT_INTERVAL]),
            )
            return

        if switch_type == "managed_dashboard":
            install_dashboard(self.hass, bool(state.get(KEY_DASHBOARD_SHOW_IN_SIDEBAR, False)))
            return

        if switch_type == "managed_sidebar":
            install_dashboard(self.hass, True)
            return

        if switch_type == "state":
            update_state(self.hass, **{self.entity_description.state_key: True})
            return

        if switch_type == "command":
            await async_send_direct_command(self.hass, self.entity_description.on_command, 1, 250)
            self._command_is_on = True
            self.async_write_ha_state()
            return

        if switch_type == "momentary_send_raw":
            async def action():
                await async_send_direct_command(
                    self.hass,
                    state[KEY_RAW_COMMAND],
                    state[KEY_REPEAT],
                    state[KEY_DELAY_MS],
                )
            await self._run_momentary(action)
            return

        if switch_type == "momentary_send_protocol":
            async def action():
                await async_send_protocol_command(
                    self.hass,
                    state[KEY_PROTOCOL_DEVICE_ID],
                    state[KEY_PROTOCOL_COMMAND],
                    state[KEY_REPEAT],
                    state[KEY_DELAY_MS],
                )
            await self._run_momentary(action)
            return

        if switch_type == "momentary_direct":
            async def action():
                await async_send_direct_command(self.hass, self.entity_description.on_command, 1, 250)
            await self._run_momentary(action)
            return

        if switch_type == "momentary_update":
            await self._run_momentary(lambda: update_from_github(self.hass))
            return

        if switch_type == "momentary_restore":
            await self._run_momentary(lambda: restore_last_update(self.hass))
            return

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off / undo."""
        switch_type = self.entity_description.switch_type

        if switch_type == "managed_prerequisite":
            remove_prerequisite(self.hass)
            return

        if switch_type == "managed_dashboard":
            remove_dashboard(self.hass)
            return

        if switch_type == "managed_sidebar":
            install_dashboard(self.hass, False)
            return

        if switch_type == "state":
            update_state(self.hass, **{self.entity_description.state_key: False})
            return

        if switch_type == "command":
            await async_send_direct_command(self.hass, self.entity_description.off_command, 1, 250)
            self._command_is_on = False
            self.async_write_ha_state()
            return

        if switch_type.startswith("momentary_"):
            self._momentary_is_on = False
            self.async_write_ha_state()
