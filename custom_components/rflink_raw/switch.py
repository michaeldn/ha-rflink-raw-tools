"""Alias-backed Home Assistant switches for RFLink Raw Tools."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .aliases import SIGNAL_ALIASES_UPDATED, async_list_aliases
from .const import DOMAIN
from .helpers import async_send_raw_command


def _is_switch_alias(alias: dict[str, Any]) -> bool:
    """Return true if an alias should be exposed as an HA switch."""
    entity_type = str(alias.get("entity_type") or "switch").lower()
    return (
        entity_type in {"switch", "light"}
        and bool(str(alias.get("on_command") or "").strip())
        and bool(str(alias.get("off_command") or "").strip())
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up alias-backed RFLink switches."""
    known: set[str] = set()

    async def _refresh_aliases() -> None:
        aliases = await async_list_aliases(hass)
        new_entities = []
        for alias in aliases:
            if not _is_switch_alias(alias):
                continue
            alias_id = str(alias.get("id") or "").strip()
            if not alias_id or alias_id in known:
                continue
            known.add(alias_id)
            new_entities.append(RFLinkAliasSwitch(hass, alias))

        if new_entities:
            async_add_entities(new_entities, True)

    await _refresh_aliases()

    @callback
    def _schedule_refresh() -> None:
        hass.async_create_task(_refresh_aliases())

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_ALIASES_UPDATED, _schedule_refresh)
    )


class RFLinkAliasSwitch(SwitchEntity, RestoreEntity):
    """Optimistic switch backed by RFLink Raw Tools alias commands."""

    _attr_should_poll = False
    _attr_icon = "mdi:radio-tower"

    def __init__(self, hass: HomeAssistant, alias: dict[str, Any]) -> None:
        """Initialize the alias switch."""
        self.hass = hass
        self._alias = alias
        self._attr_unique_id = f"{DOMAIN}_alias_{alias['id']}"
        self._attr_name = str(alias.get("name") or alias["id"])
        self._is_on = False

    @property
    def is_on(self) -> bool:
        """Return optimistic switch state."""
        return self._is_on

    @property
    def available(self) -> bool:
        """Return true when both RFLink commands are available."""
        return bool(self._alias.get("on_command") and self._alias.get("off_command"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose alias details for diagnostics."""
        return {
            "rflink_raw_alias_id": self._alias.get("id"),
            "rflink_device_id": self._alias.get("device_id"),
            "on_command": self._alias.get("on_command"),
            "off_command": self._alias.get("off_command"),
            "source_packet": self._alias.get("source_packet"),
            "notes": self._alias.get("notes"),
            "optimistic_state": True,
        }

    async def async_added_to_hass(self) -> None:
        """Restore optimistic state after restart."""
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._is_on = last_state.state == "on"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Send the alias ON command."""
        await async_send_raw_command(
            self.hass,
            str(self._alias["on_command"]),
            repeat=1,
            delay_ms=250,
        )
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Send the alias OFF command."""
        await async_send_raw_command(
            self.hass,
            str(self._alias["off_command"]),
            repeat=1,
            delay_ms=250,
        )
        self._is_on = False
        self.async_write_ha_state()
