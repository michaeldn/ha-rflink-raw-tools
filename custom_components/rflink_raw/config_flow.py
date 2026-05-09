"""Config flow for RFLink Raw Tools."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    KEY_DASHBOARD_REQUIRE_ADMIN,
    KEY_DASHBOARD_SHOW_IN_SIDEBAR,
    KEY_PREREQ_PORT,
    KEY_PREREQ_RECONNECT_INTERVAL,
    KEY_PREREQ_WAIT_FOR_ACK,
    NAME,
)
from .dashboard import install_dashboard_registration
from .prereq import install_rflink_prerequisite


class RFLinkRawConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RFLink Raw Tools."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""
        await self.async_set_unique_id("rflink_raw_tools")
        self._abort_if_unique_id_configured()

        errors = {}

        if user_input is not None:
            if user_input.get("install_prerequisite"):
                try:
                    install_rflink_prerequisite(
                        self.hass,
                        user_input[KEY_PREREQ_PORT],
                        user_input[KEY_PREREQ_WAIT_FOR_ACK],
                        user_input[KEY_PREREQ_RECONNECT_INTERVAL],
                    )
                except Exception:
                    errors["base"] = "prerequisite_install_failed"

            if not errors and user_input.get("install_dashboard"):
                try:
                    install_dashboard_registration(
                        self.hass,
                        user_input.get(KEY_DASHBOARD_SHOW_IN_SIDEBAR, True),
                        user_input.get(KEY_DASHBOARD_REQUIRE_ADMIN, False),
                    )
                except Exception:
                    errors["base"] = "dashboard_install_failed"

            if not errors:
                return self.async_create_entry(title=NAME, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional("install_prerequisite", default=True): bool,
                    vol.Optional(KEY_PREREQ_PORT, default="/dev/ttyUSB0"): str,
                    vol.Optional(KEY_PREREQ_WAIT_FOR_ACK, default=False): bool,
                    vol.Optional(KEY_PREREQ_RECONNECT_INTERVAL, default=10): int,
                    vol.Optional("install_dashboard", default=True): bool,
                    vol.Optional(KEY_DASHBOARD_SHOW_IN_SIDEBAR, default=True): bool,
                    vol.Optional(KEY_DASHBOARD_REQUIRE_ADMIN, default=False): bool,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return RFLinkRawOptionsFlow(config_entry)


class RFLinkRawOptionsFlow(config_entries.OptionsFlow):
    """Handle RFLink Raw Tools options."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        errors = {}

        if user_input is not None:
            if user_input.get("install_prerequisite"):
                try:
                    install_rflink_prerequisite(
                        self.hass,
                        user_input[KEY_PREREQ_PORT],
                        user_input[KEY_PREREQ_WAIT_FOR_ACK],
                        user_input[KEY_PREREQ_RECONNECT_INTERVAL],
                    )
                except Exception:
                    errors["base"] = "prerequisite_install_failed"

            if not errors and user_input.get("install_dashboard"):
                try:
                    install_dashboard_registration(
                        self.hass,
                        user_input.get(KEY_DASHBOARD_SHOW_IN_SIDEBAR, True),
                        user_input.get(KEY_DASHBOARD_REQUIRE_ADMIN, False),
                    )
                except Exception:
                    errors["base"] = "dashboard_install_failed"

            if not errors:
                return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("install_prerequisite", default=False): bool,
                    vol.Optional(
                        KEY_PREREQ_PORT,
                        default=current.get(KEY_PREREQ_PORT, "/dev/ttyUSB0"),
                    ): str,
                    vol.Optional(
                        KEY_PREREQ_WAIT_FOR_ACK,
                        default=current.get(KEY_PREREQ_WAIT_FOR_ACK, False),
                    ): bool,
                    vol.Optional(
                        KEY_PREREQ_RECONNECT_INTERVAL,
                        default=current.get(KEY_PREREQ_RECONNECT_INTERVAL, 10),
                    ): int,
                    vol.Optional("install_dashboard", default=False): bool,
                    vol.Optional(
                        KEY_DASHBOARD_SHOW_IN_SIDEBAR,
                        default=current.get(KEY_DASHBOARD_SHOW_IN_SIDEBAR, True),
                    ): bool,
                    vol.Optional(
                        KEY_DASHBOARD_REQUIRE_ADMIN,
                        default=current.get(KEY_DASHBOARD_REQUIRE_ADMIN, False),
                    ): bool,
                }
            ),
            errors=errors,
        )
