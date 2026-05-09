"""Sensor platform for RFLink Raw Tools."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription

from .const import (
    COMMAND_DEVICE_IDENTIFIER,
    COMMAND_DEVICE_NAME,
    DEVICE_IDENTIFIER,
    DEVICE_NAME,
    DOMAIN,
    KEY_DASHBOARD_STATUS,
    KEY_LAST_COMMAND,
    KEY_LAST_ERROR,
    KEY_LAST_RESPONSE,
    KEY_PREREQ_STATUS,
    KEY_UPDATE_STATUS,
    MANUFACTURER,
    MODEL,
    VERSION,
)
from .store import get_state


@dataclass(frozen=True, kw_only=True)
class RFLinkRawSensorDescription(EntityDescription):
    """Description for an RFLink Raw Tools sensor."""

    state_key: str
    entity_category: str | None = "diagnostic"
    enabled_default: bool = False
    device_area: str = "admin"


SENSORS: tuple[RFLinkRawSensorDescription, ...] = (
    RFLinkRawSensorDescription(key="status_prereq_status", name="Status RFLink Prerequisite Status", icon="mdi:file-check-outline", state_key=KEY_PREREQ_STATUS),
    RFLinkRawSensorDescription(key="status_dashboard_status", name="Status RFLink Dashboard Status", icon="mdi:view-dashboard-outline", state_key=KEY_DASHBOARD_STATUS),
    RFLinkRawSensorDescription(key="status_update_status", name="Status RFLink Update Status", icon="mdi:update", state_key=KEY_UPDATE_STATUS),
    RFLinkRawSensorDescription(key="status_last_command", name="Status RFLink Last Command", icon="mdi:history", state_key=KEY_LAST_COMMAND, device_area="command"),
    RFLinkRawSensorDescription(key="status_last_response", name="Status RFLink Last Response", icon="mdi:message-reply-text", state_key=KEY_LAST_RESPONSE, device_area="command"),
    RFLinkRawSensorDescription(key="status_last_error", name="Status RFLink Last Error", icon="mdi:alert-circle-outline", state_key=KEY_LAST_ERROR, device_area="command"),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up RFLink Raw Tools sensors."""
    async_add_entities(RFLinkRawSensor(hass, entry.entry_id, description) for description in SENSORS)


class RFLinkRawSensor(SensorEntity):
    """RFLink Raw Tools sensor."""

    _attr_has_entity_name = False

    def __init__(self, hass, entry_id: str, description: RFLinkRawSensorDescription) -> None:
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

    @property
    def native_value(self) -> str:
        """Return sensor value."""
        value = get_state(self.hass).get(self.entity_description.state_key, "")
        if len(value) > 250:
            return value[:247] + "..."
        return value
