"""Minimal config flow for diagnosis."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN


class TauronCostConfigFlow(ConfigFlow, domain=DOMAIN):
    """Minimal flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="Tauron Cost", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))
