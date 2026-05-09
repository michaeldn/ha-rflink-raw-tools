"""Simple in-memory state store for RFLink Raw Tools."""

from __future__ import annotations

from datetime import datetime

from homeassistant.core import HomeAssistant, callback

from .const import (
    DATA_STATE,
    DOMAIN,
    KEY_LAST_COMMAND,
    KEY_LAST_ERROR,
    KEY_LAST_RESPONSE,
    KEY_PROTOCOL_COMMAND,
    KEY_PROTOCOL_DEVICE_ID,
    KEY_RAW_COMMAND,
)


DEFAULT_STATE = {
    KEY_RAW_COMMAND: "10;PING;",
    KEY_PROTOCOL_DEVICE_ID: "",
    KEY_PROTOCOL_COMMAND: "on",
    KEY_LAST_COMMAND: "",
    KEY_LAST_RESPONSE: "",
    KEY_LAST_ERROR: "",
}


@callback
def get_state(hass: HomeAssistant) -> dict:
    """Get integration state."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    state = domain_data.setdefault(DATA_STATE, DEFAULT_STATE.copy())
    return state


@callback
def update_state(hass: HomeAssistant, **kwargs) -> None:
    """Update integration state."""
    state = get_state(hass)
    state.update(kwargs)


def timestamped(value: str) -> str:
    """Return a timestamped state value."""
    return f"{datetime.now().isoformat(timespec='seconds')} — {value}"
