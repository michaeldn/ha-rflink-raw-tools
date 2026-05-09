"""Text platform for RFLink Raw Tools."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription

from .const import (
    DEVICE_IDENTIFIER,
    DEVICE_NAME,
    DOMAIN,
    KEY_PREREQ_PORT,
    KEY_PROTOCOL_COMMAND,
    KEY_PROTOCOL_DEVICE_ID,
    KEY_RAW_COMMAND,
    MANUFACTURER,
    MODEL,
    VERSION,
)
from .store import get_state, update_state


@dataclass(frozen=True, kw_only=True)
class RFLinkRawTextDescription(EntityDescription):
    """Description for an RFLink Raw Tools text entity."""

    state_key: str
    native_max: int = 255
    entity_category: str | None = "config"


TEXTS: tuple[RFLinkRawTextDescription, ...] = (
    RFLinkRawTextDescription(key="setup_prereq_port", name="Setup RFLink Prerequisite Port", icon="mdi:serial-port", state_key=KEY_PREREQ_PORT, native_max=255),
    RFLinkRawTextDescription(key="control_raw_command", name="Control RFLink Raw Command", icon="mdi:code-string", state_key=KEY_RAW_COMMAND, native_max=2048),
    RFLinkRawTextDescription(key="control_protocol_device_id", name="Control RFLink Protocol Device ID", icon="mdi:identifier", state_key=KEY_PROTOCOL_DEVICE_ID, native_max=255),
    RFLinkRawTextDescription(key="control_protocol_command", name="Control RFLink Protocol Command", icon="mdi:gesture-tap-button", state_key=KEY_PROTOCOL_COMMAND, native_max=80),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up RFLink Raw Tools text entities."""
    async_add_entities(RFLinkRawText(hass, entry.entry_id, description) for description in TEXTS)


class RFLinkRawText(TextEntity):
    """RFLink Raw Tools text entity."""

    _attr_has_entity_name = False
    _attr_mode = TextMode.TEXT

    def __init__(self, hass, entry_id: str, description: RFLinkRawTextDescription) -> None:
        self.hass = hass
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_entity_category = description.entity_category
        self._attr_native_max = description.native_max
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DEVICE_IDENTIFIER)},
            name=DEVICE_NAME,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=VERSION,
        )

    @property
    def native_value(self) -> str:
        """Return the text value."""
        return get_state(self.hass).get(self.entity_description.state_key, "")

    async def async_set_value(self, value: str) -> None:
        """Set text value."""
        update_state(self.hass, **{self.entity_description.state_key: value})
        self.async_write_ha_state()
