"""Derive and extend Tauron cost statistics from the importer's zone data."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    get_last_statistics,
    list_statistic_ids,
    statistics_during_period,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    CURRENCY,
    DETECT_SUFFIX,
    DOMAIN,
    IMPORTER_SOURCE,
    SERIES,
    CostSeries,
)

_LOGGER = logging.getLogger(__name__)


async def async_detect_prefix(hass: HomeAssistant) -> str | None:
    """Find the Tauron AMIplus importer prefix, e.g. 'tauron_importer:123_..._'."""
    ids = await get_instance(hass).async_add_executor_job(
        list_statistic_ids, hass, None, "sum"
    )
    for item in ids:
        sid = item["statistic_id"]
        if sid.startswith(f"{IMPORTER_SOURCE}:") and sid.endswith(DETECT_SUFFIX):
            return sid[: -len(DETECT_SUFFIX)]
    return None


def _to_dt(start) -> datetime:
    """Recorder 'start' may be a float timestamp or a datetime; normalise to UTC."""
    if isinstance(start, (int, float)):
        return dt_util.utc_from_timestamp(start)
    return dt_util.as_utc(start)


async def _last_cost(hass: HomeAssistant, statistic_id: str) -> tuple[datetime | None, float]:
    """Return (last point start, cumulative sum) for a cost statistic, or (None, 0)."""
    last = await get_instance(hass).async_add_executor_job(
        get_last_statistics, hass, 1, statistic_id, True, {"sum"}
    )
    rows = last.get(statistic_id)
    if not rows:
        return None, 0.0
    row = rows[0]
    return _to_dt(row["start"]), float(row.get("sum") or 0.0)


async def _importer_changes(
    hass: HomeAssistant, statistic_id: str, start: datetime
) -> list[tuple[datetime, float]]:
    """Hourly (start, change) for an importer statistic from `start` onward."""
    result = await get_instance(hass).async_add_executor_job(
        statistics_during_period,
        hass,
        start,
        None,
        {statistic_id},
        "hour",
        None,
        {"change"},
    )
    out: list[tuple[datetime, float]] = []
    for row in result.get(statistic_id, []):
        change = row.get("change")
        if change is None:
            continue
        out.append((_to_dt(row["start"]), float(change)))
    return out


async def async_update_series(
    hass: HomeAssistant, prefix: str, series: CostSeries, price: float
) -> int:
    """Extend one cost statistic with new hours of importer data x price."""
    cost_id = f"{DOMAIN}:{series.cost_key}"
    importer_id = f"{prefix}{series.importer_suffix}"

    last_start, running = await _last_cost(hass, cost_id)
    # Read importer data strictly after the last cost hour (or from the start).
    read_from = (last_start + timedelta(hours=1)) if last_start else dt_util.utc_from_timestamp(0)

    changes = await _importer_changes(hass, importer_id, read_from)
    if not changes:
        return 0

    points: list[StatisticData] = []
    for start, change in changes:
        value = change * price
        running += value
        points.append(StatisticData(start=start, state=round(value, 4), sum=round(running, 4)))

    metadata = StatisticMetaData(
        mean_type=StatisticMeanType.NONE,
        has_sum=True,
        name=series.name,
        source=DOMAIN,
        statistic_id=cost_id,
        unit_of_measurement=CURRENCY,
        unit_class=None,
    )
    async_add_external_statistics(hass, metadata, points)
    return len(points)


async def async_update_all(hass: HomeAssistant, prefix: str, prices: dict[str, float]) -> int:
    """Extend all four cost statistics. Returns total points written."""
    total = 0
    for series in SERIES:
        price = prices.get(series.price_option, series.default_price)
        try:
            total += await async_update_series(hass, prefix, series, price)
        except Exception:  # noqa: BLE001 - one bad series must not stop the rest
            _LOGGER.exception("Failed updating cost series %s", series.cost_key)
    if total:
        _LOGGER.info("Tauron cost: wrote %s new hourly points", total)
    return total
