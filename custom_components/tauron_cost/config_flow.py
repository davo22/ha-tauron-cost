"""Config flow for the Tauron Cost integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_CREDIT_T1,
    CONF_CREDIT_T2,
    CONF_PRICE_T1,
    CONF_PRICE_T2,
    DEFAULT_CREDIT_T1,
    DEFAULT_CREDIT_T2,
    DEFAULT_PRICE_T1,
    DEFAULT_PRICE_T2,
    DOMAIN,
)

PRICE_FIELDS = (
    (CONF_PRICE_T1, DEFAULT_PRICE_T1),
    (CONF_PRICE_T2, DEFAULT_PRICE_T2),
    (CONF_CREDIT_T1, DEFAULT_CREDIT_T1),
    (CONF_CREDIT_T2, DEFAULT_CREDIT_T2),
)


def _price_schema(current: dict[str, Any]) -> vol.Schema:
    price = NumberSelector(
        NumberSelectorConfig(min=0, step=0.0001, mode=NumberSelectorMode.BOX)
    )
    return vol.Schema(
        {
            vol.Required(key, default=current.get(key, default)): price
            for key, default in PRICE_FIELDS
        }
    )


class TauronCostConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Tauron Cost config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return TauronCostOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect the zone prices. The Tauron importer is found at setup time."""
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Tauron Cost", options=dict(user_input))

        return self.async_show_form(step_id="user", data_schema=_price_schema({}))


class TauronCostOptionsFlow(OptionsFlow):
    """Edit the zone prices (rebuilds cost statistics on save)."""

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init", data_schema=_price_schema(dict(self.config_entry.options))
        )
