"""The Tauron Cost integration — keeps zone cost statistics current."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_PREFIX,
    DOMAIN,
    SERIES,
    SERVICE_RECALCULATE,
)
from .statistics import async_update_all

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(hours=6)

TauronCostEntry = ConfigEntry


def _prices(entry: TauronCostEntry) -> dict[str, float]:
    """Current unit prices, options overriding the per-series defaults."""
    prices = {s.price_option: s.default_price for s in SERIES}
    for key in prices:
        if key in entry.options:
            prices[key] = float(entry.options[key])
    return prices


async def async_setup_entry(hass: HomeAssistant, entry: TauronCostEntry) -> bool:
    """Set up Tauron Cost from a config entry."""
    prefix = entry.data[CONF_PREFIX]

    async def _refresh(_now=None) -> None:
        try:
            await async_update_all(hass, prefix, _prices(entry))
        except Exception:  # noqa: BLE001 - scheduled task must not die silently
            _LOGGER.exception("Tauron cost refresh failed")

    # Catch up now, then on a timer.
    await _refresh()
    entry.async_on_unload(async_track_time_interval(hass, _refresh, UPDATE_INTERVAL))
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    _register_service(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TauronCostEntry) -> bool:
    """Unload a config entry."""
    return True


async def _async_options_updated(hass: HomeAssistant, entry: TauronCostEntry) -> None:
    """Rewrite cost statistics after a price change, then catch up to now.

    Changing a price means the whole series must be recomputed, so the existing
    cost statistics are cleared first and rebuilt from the importer history.
    """
    from homeassistant.components.recorder import get_instance
    from homeassistant.components.recorder.statistics import clear_statistics

    ids = [f"{DOMAIN}:{s.cost_key}" for s in SERIES]
    await get_instance(hass).async_add_executor_job(clear_statistics, get_instance(hass), ids)
    await async_update_all(hass, entry.data[CONF_PREFIX], _prices(entry))


def _register_service(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_RECALCULATE):
        return

    async def _handle(call: ServiceCall) -> None:
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            await async_update_all(hass, entry.data[CONF_PREFIX], _prices(entry))

    hass.services.async_register(DOMAIN, SERVICE_RECALCULATE, _handle)
