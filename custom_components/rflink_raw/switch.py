"""Switch platform for RFLink Raw Tools."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory, EntityDescription

from .const import (
    DEVICE_IDENTIFIER,
    DEVICE_NAME,
    DOMAIN,
    KEY_DASHBOARD_REQUIRE_ADMIN,
    KEY_DASHBOARD_SHOW_IN_SIDEBAR,
    KEY_PREREQ_WAIT_FOR_ACK,
    MANUFACTURER,
    MODEL,
    VERSION,
)
from .helpers import async_send_direct_command
from .store import get_state, update_state


@dataclass(frozen=True, kw_only=True)
class RFLinkRawSwitchDescription(EntityDescription):
    """Description for an RFLink Raw Tools switch."""

    state_key: str | None = None
    switch_type: str = "command"
    on_command: str | None = None
    off_command: str | None = None


SWITCHES: tuple[RFLinkRawSwitchDescription, ...] = (
    RFLinkRawSwitchDescription(
        key="dashboard_show_in_sidebar",
        name="Dashboard Show In Sidebar",
        icon="mdi:menu-open",
        state_key=KEY_DASHBOARD_SHOW_IN_SIDEBAR,
        switch_type="state",
        entity_category=EntityCategory.CONFIG,
    ),
    RFLinkRawSwitchDescription(
        key="dashboard_require_admin",
        name="Dashboard Require Admin",
        icon="mdi:shield-account-outline",
        state_key=KEY_DASHBOARD_REQUIRE_ADMIN,
        switch_type="state",
        entity_category=EntityCategory.CONFIG,
    ),
    RFLinkRawSwitchDescription(
        key="setup_prereq_wait_for_ack",
        name="Setup RFLink Prerequisite Wait For ACK",
        icon="mdi:handshake-outline",
        state_key=KEY_PREREQ_WAIT_FOR_ACK,
        switch_type="state",
        entity_category=EntityCategory.CONFIG,
    ),
    RFLinkRawSwitchDescription(
        key="debug_rfdebug",
        name="Debug RFLink RFDEBUG",
        icon="mdi:radio-tower",
        on_command="10;RFDEBUG=ON;",
        off_command="10;RFDEBUG=OFF;",
    ),
    RFLinkRawSwitchDescription(
        key="debug_qrfdebug",
        name="Debug RFLink QRFDEBUG",
        icon="mdi:signal",
        on_command="10;QRFDEBUG=ON;",
        off_command="10;QRFDEBUG=OFF;",
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
        self._attr_is_on = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DEVICE_IDENTIFIER)},
            name=DEVICE_NAME,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=VERSION,
        )

    @property
    def is_on(self) -> bool:
        """Return switch state."""
        if self.entity_description.switch_type == "state":
            return bool(get_state(self.hass).get(self.entity_description.state_key, False))
        return bool(self._attr_is_on)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on."""
        if self.entity_description.switch_type == "state":
            update_state(self.hass, **{self.entity_description.state_key: True})
        else:
            await async_send_direct_command(self.hass, self.entity_description.on_command, 1, 250)
            self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off."""
        if self.entity_description.switch_type == "state":
            update_state(self.hass, **{self.entity_description.state_key: False})
        else:
            await async_send_direct_command(self.hass, self.entity_description.off_command, 1, 250)
            self._attr_is_on = False
        self.async_write_ha_state()
