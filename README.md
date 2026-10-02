# Tauron Cost (zone pricing) — Home Assistant

Keeps **electricity cost statistics** for the Energy dashboard current when your
consumption comes from the [Tauron AMIplus](https://github.com/PiotrMachowski/Home-Assistant-custom-components-Tauron-AMIplus)
integration.

## Why this exists

Tauron AMIplus publishes consumption as **external statistics**. Home Assistant
does **not** allow a fixed per-kWh price on an external-statistic grid source —
it requires a pre-computed **cost statistic**. Such a statistic, built once by
hand, never gets extended, so after a few days the Energy dashboard stops showing
electricity cost. This integration computes `consumption × zone price` hourly and
appends it to `tauron_cost:*` statistics on a timer, so the cost never freezes.

It is zone-aware for **G12** (two tariff zones): separate import prices for day
(T1) and night (T2), plus the net-metering credit value (opust) per zone.

## Requirements

- Home Assistant 2025.8.0+
- The **Tauron AMIplus** integration set up and having imported zone statistics
  (`balanced_consumption_zone_1/2`, `balanced_generation_zone_1/2`).

## Setup

1. Install via HACS (custom repository, category "Integration"), restart.
2. Settings → Devices & Services → Add Integration → **Tauron Cost**.
   The Tauron importer is detected automatically; enter your four PLN/kWh prices
   (defaults are placeholders — use your own from the invoice).

The cost statistics (`tauron_cost:cost_zone_1/2`, `credit_zone_1/2`) are then
updated every few hours. Wire them in the Energy dashboard as the grid source's
cost / compensation.

Change prices anytime via **Configure** — the cost history is rebuilt. The
`tauron_cost.recalculate` service forces an immediate catch-up.

## Notes

- Prices are fixed values you enter; this does not fetch live prices.
- Only reads statistics and writes derived ones; it never touches your meter or
  the Tauron account.
- Not affiliated with Tauron or the Tauron AMIplus integration.
