"""Config flow for RFLink Raw Tools."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, NAME


class RFLinkRawConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RFLink Raw Tools."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        await self.async_set_unique_id("rflink_raw_tools")
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title=NAME, data={})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return no options flow."""
        return None
