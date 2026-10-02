"""Constants for the Tauron Cost integration."""
from __future__ import annotations

from dataclasses import dataclass

DOMAIN = "tauron_cost"

# Tauron AMIplus publishes zone consumption/generation as external statistics
# named "<prefix>balanced_consumption_zone_1" etc. We derive a cost statistic
# per zone and keep it current, because Home Assistant does not allow a fixed
# per-kWh price on an external-statistic grid source — it demands a cost
# statistic, which otherwise never gets extended.
IMPORTER_SOURCE = "tauron_importer"
DETECT_SUFFIX = "balanced_consumption_zone_1"

CONF_PREFIX = "importer_prefix"
CONF_PRICE_T1 = "price_t1"
CONF_PRICE_T2 = "price_t2"
CONF_CREDIT_T1 = "credit_t1"
CONF_CREDIT_T2 = "credit_t2"
CURRENCY = "PLN"

# Defaults from Dawid's invoice (brutto). Editable in the options flow.
DEFAULT_PRICE_T1 = 1.0770
DEFAULT_PRICE_T2 = 0.6363
DEFAULT_CREDIT_T1 = 0.8515
DEFAULT_CREDIT_T2 = 0.4989

SERVICE_RECALCULATE = "recalculate"


@dataclass(frozen=True)
class CostSeries:
    """One derived cost statistic: importer consumption/generation x price."""

    cost_key: str  # statistic id suffix, e.g. "cost_zone_1"
    importer_suffix: str  # importer statistic suffix to read
    price_option: str  # options key holding the unit price
    default_price: float
    name: str


SERIES: tuple[CostSeries, ...] = (
    CostSeries("cost_zone_1", "balanced_consumption_zone_1", CONF_PRICE_T1, DEFAULT_PRICE_T1, "Tauron koszt T1"),
    CostSeries("cost_zone_2", "balanced_consumption_zone_2", CONF_PRICE_T2, DEFAULT_PRICE_T2, "Tauron koszt T2"),
    CostSeries("credit_zone_1", "balanced_generation_zone_1", CONF_CREDIT_T1, DEFAULT_CREDIT_T1, "Tauron opust T1"),
    CostSeries("credit_zone_2", "balanced_generation_zone_2", CONF_CREDIT_T2, DEFAULT_CREDIT_T2, "Tauron opust T2"),
)
