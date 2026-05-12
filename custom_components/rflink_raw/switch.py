"""Switch entities for RFLink Raw Tools aliases."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .aliases import SIGNAL_ALIASES_UPDATED, async_list_aliases
from .const import DOMAIN, NAME
from .helpers import async_send_raw_command


def _is_switch_alias(alias: dict[str, Any]) -> bool:
    return alias.get("entity_type") in {"switch", "light"} and bool(alias.get("on_command"))


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up RFLink Raw Tools alias switches."""
    entities: dict[str, RFLinkRawAliasSwitch] = {}

    async def async_refresh_aliases() -> None:
        aliases = [alias for alias in await async_list_aliases(hass) if _is_switch_alias(alias)]
        seen = {alias["id"] for alias in aliases}

        for alias in aliases:
            alias_id = alias["id"]
            if alias_id in entities:
                entities[alias_id].update_alias(alias)
                entities[alias_id].async_write_ha_state()
            else:
                entity = RFLinkRawAliasSwitch(hass, alias)
                entities[alias_id] = entity
                async_add_entities([entity])

        for alias_id, entity in list(entities.items()):
            if alias_id not in seen:
                await entity.async_remove()
                entities.pop(alias_id, None)

    await async_refresh_aliases()

    @callback
    def _handle_update() -> None:
        hass.async_create_task(async_refresh_aliases())

    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_ALIASES_UPDATED, _handle_update))


class RFLinkRawAliasSwitch(SwitchEntity):
    """Switch backed by an RFLink Raw Tools alias."""

    _attr_has_entity_name = False

    def __init__(self, hass: HomeAssistant, alias: dict[str, Any]) -> None:
        self.hass = hass
        self._alias = alias
        self._attr_unique_id = f"rflink_raw_alias_{alias['id']}"
        self._attr_name = alias["name"]
        self._attr_icon = "mdi:remote"
        self._is_on = False

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, f"alias_{self._alias['id']}")},
            "name": self._alias["name"],
            "manufacturer": NAME,
            "model": "RFLink Alias",
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "rflink_device_id": self._alias.get("device_id", ""),
            "on_command": self._alias.get("on_command", ""),
            "off_command": self._alias.get("off_command", ""),
            "source_packet": self._alias.get("source_packet", ""),
            "notes": self._alias.get("notes", ""),
        }

    def update_alias(self, alias: dict[str, Any]) -> None:
        self._alias = alias
        self._attr_name = alias["name"]

    async def async_turn_on(self, **kwargs: Any) -> None:
        command = self._alias.get("on_command")
        if not command:
            raise HomeAssistantError("This RFLink alias has no ON command.")
        await async_send_raw_command(self.hass, command)
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        command = self._alias.get("off_command")
        if not command:
            raise HomeAssistantError("This RFLink alias has no OFF command.")
        await async_send_raw_command(self.hass, command)
        self._is_on = False
        self.async_write_ha_state()
