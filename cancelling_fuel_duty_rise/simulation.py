"""Run the PolicyEngine UK simulations behind the briefing.

Everything downstream (charts, tables, build scripts) consumes the artefacts
produced by :func:`compute_all`. The simulation is expensive so results are
memoised per process.

Design notes
------------
- The simulation entry point is the unified ``policyengine`` package via
  :func:`policyengine.tax_benefit_models.uk.managed_microsimulation`. The
  installed ``policyengine-uk`` package is pinned to the certified
  ``policyengine.py`` UK bundle while the fuel uprating branch awaits release.
- Fiscal totals are benchmarked to HMRC/OBR road-fuel litre controls. The
  PolicyEngine microsimulation provides distributional allocation, which is
  scaled to those fiscal controls.
- All weighted aggregates use the native ``microdf`` API. The package never
  multiplies values by weights by hand.
"""

from __future__ import annotations

import functools
import os
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .historical import (
    FISCAL_YEAR_AVERAGE_DUTY_RATE,
    FIRST_FREEZE_YEAR,
    OBR_FORECAST_VINTAGE,
    benchmark_cost_bn,
    benchmark_receipts_bn,
    hmrc_receipts_bn,
    road_fuel_clearances_mlitres,
)

DEFAULT_DATASET_NAME = "enhanced_frs_2023_24"
DEFAULT_DATASET_FILENAME = "enhanced_frs_2023_24.h5"
DEFAULT_DATASET_REPO = "policyengine/policyengine-uk-data-private"
DEFAULT_DATASET_REPO_TYPE = "model"
DEFAULT_DATASET_REVISION = os.environ.get("POLICYENGINE_UK_DATA_REVISION", "1.55.5")
DEFAULT_DATASET_METHOD_NOTE = (
    "released UK-data build; fuel-spending training will use the litre-proxy "
    "method after policyengine-uk-data#404 is released and rebuilt"
)
DEFAULT_DATASET_URI = (
    f"hf://{DEFAULT_DATASET_REPO}/{DEFAULT_DATASET_FILENAME}@{DEFAULT_DATASET_REVISION}"
)
DEFAULT_ANALYSIS_YEARS = list(range(2023, 2030))


def _default_storage_dir() -> str:
    """Pick a writable cache directory for downloaded datasets."""
    custom = os.environ.get("CANCELLING_FUEL_DUTY_RISE_DATA_DIR")
    if custom:
        return os.path.expanduser(custom)
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = xdg if xdg else os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(base, "cancelling-fuel-duty-rise")


def _policyengine_version() -> str:
    """Return the installed ``policyengine`` Python package version."""
    from importlib.metadata import version

    return version("policyengine")


def _fiscal_year_average_rate(parameter, year: int) -> float:
    """Average a dated PolicyEngine rate over a UK fiscal year."""
    if year in FISCAL_YEAR_AVERAGE_DUTY_RATE:
        return FISCAL_YEAR_AVERAGE_DUTY_RATE[year]
    return float(parameter(f"{year}-06-01"))


def _dataset_years(dataset_reference: str) -> list[int]:
    """Infer fiscal years from an enhanced FRS multi-year filename."""
    match = re.search(r"_(\d{4})_(\d{2})(?:\.h5)?(?:@|$)", dataset_reference)
    if not match:
        raise ValueError(f"Cannot infer dataset years from {dataset_reference}")
    first_year = int(match.group(1))
    last_year = int(f"{str(first_year)[:2]}{match.group(2)}")
    return list(range(first_year, last_year + 1))


@dataclass
class Results:
    """All numbers needed to draw the report."""

    data_years: list[int]
    scrap_5p: pd.DataFrame
    guardian_check: pd.DataFrame
    rate_history: pd.DataFrame
    rate_path: pd.DataFrame
    revenue_2010_2029: pd.DataFrame
    quartiles: pd.DataFrame
    quintiles: pd.DataFrame
    deciles: pd.DataFrame
    headline: dict
    policyengine_version: str
    citation: str


@functools.lru_cache(maxsize=1)
def compute_all(
    dataset_path: str | None = None,
    year_dist: int = 2027,
    hf_token: str | None = None,
) -> Results:
    """Run all simulations once and return the bundled :class:`Results`."""
    if hf_token:
        os.environ["HUGGING_FACE_TOKEN"] = hf_token

    from importlib.metadata import PackageNotFoundError, version as _pkg_version

    from policyengine.tax_benefit_models.uk import managed_microsimulation, uk_latest

    dataset_reference = dataset_path or DEFAULT_DATASET_NAME
    data_years = (
        _dataset_years(dataset_reference)
        if dataset_path is not None
        else DEFAULT_ANALYSIS_YEARS
    )
    first_year, last_year = min(data_years), max(data_years)
    reform_window = f"{first_year}-01-01.{last_year}-12-31"

    def _sim(*, reform: dict | None = None):
        kwargs = {"reform": reform} if reform is not None else {}
        return managed_microsimulation(
            dataset=dataset_reference,
            allow_unmanaged="://" in dataset_reference,
            **kwargs,
        )

    baseline_sim = _sim()
    params = baseline_sim.tax_benefit_system.parameters
    fuel_duty = params.gov.hmrc.fuel_duty.petrol_and_diesel
    rpi = params.gov.economic_assumptions.yoy_growth.obr.rpi

    pre_cut_rate = fuel_duty(f"{FIRST_FREEZE_YEAR}-04-01")
    post_cut_rate = fuel_duty(_find_cut_date(fuel_duty))

    keep_cut_sim = _sim(
        reform={"gov.hmrc.fuel_duty.petrol_and_diesel": {reform_window: post_cut_rate}},
    )

    counterfactual_rate = {FIRST_FREEZE_YEAR: pre_cut_rate}
    for year in range(FIRST_FREEZE_YEAR + 1, last_year + 1):
        counterfactual_rate[year] = counterfactual_rate[year - 1] * (
            1 + rpi(f"{year}-01-01")
        )
    actual_rate = {
        year: _fiscal_year_average_rate(fuel_duty, year)
        for year in range(FIRST_FREEZE_YEAR, last_year + 1)
    }

    road_fuel_years = road_fuel_clearances_mlitres(end_year=last_year)
    first_road_fuel_year = min(road_fuel_years)

    def rate_gap_cost_bn(
        year: int,
        rate_gap: float,
        current_rate: float,
    ) -> float:
        if year >= first_road_fuel_year:
            return benchmark_cost_bn(year, rate_gap)
        return benchmark_receipts_bn(year, current_rate) * rate_gap / current_rate

    def revenue_at_rate(year: int, rate: float) -> float:
        current_law = benchmark_receipts_bn(year, actual_rate[year])
        return current_law + rate_gap_cost_bn(
            year, rate - actual_rate[year], actual_rate[year]
        )

    scrap_5p = pd.DataFrame(
        [
            {
                "Year": year,
                "Baseline rate (p/L)": round(actual_rate[year] * 100, 2),
                "Baseline revenue (£bn)": round(
                    revenue_at_rate(year, actual_rate[year]), 2
                ),
                "Reform revenue (£bn)": round(revenue_at_rate(year, post_cut_rate), 2),
                "Cost to Treasury (£bn)": round(
                    benchmark_cost_bn(year, actual_rate[year] - post_cut_rate),
                    2,
                ),
            }
            for year in data_years
        ]
    )

    guardian_check = pd.DataFrame(
        [
            {
                "Year": year,
                "Revenue at 52.95p (£bn)": round(
                    revenue_at_rate(year, post_cut_rate), 2
                ),
                "Revenue at 57.95p (£bn)": round(
                    revenue_at_rate(year, pre_cut_rate), 2
                ),
                "Cost of keeping 5p cut (£bn)": round(
                    benchmark_cost_bn(year, pre_cut_rate - post_cut_rate),
                    2,
                ),
            }
            for year in data_years
        ]
    )

    rate_history = (
        pd.DataFrame(
            [
                {
                    "date": value.instant_str,
                    "rate_per_litre_gbp": value.value,
                    "rate_pence_per_litre": round(value.value * 100, 4),
                }
                for value in fuel_duty.values_list
            ]
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    rate_path = pd.DataFrame(
        [
            {
                "year": year,
                "rpi_yoy_growth_pct": round(rpi(f"{year}-01-01") * 100, 4),
                "actual_rate_p_per_litre": round(actual_rate[year] * 100, 4),
                "rpi_counterfactual_rate_p_per_litre": round(
                    counterfactual_rate[year] * 100, 4
                ),
                "gap_p_per_litre": round(
                    (counterfactual_rate[year] - actual_rate[year]) * 100, 4
                ),
            }
            for year in sorted(counterfactual_rate)
        ]
    )

    hmrc_bn = hmrc_receipts_bn()
    earliest_year = min(hmrc_bn)
    counterfactual_rate_full = {earliest_year: fuel_duty(f"{earliest_year}-04-01")}
    for year in range(earliest_year + 1, last_year + 1):
        counterfactual_rate_full[year] = counterfactual_rate_full[year - 1] * (
            1 + rpi(f"{year}-01-01")
        )
    actual_rate_full = {
        year: _fiscal_year_average_rate(fuel_duty, year)
        for year in range(earliest_year, last_year + 1)
    }
    revenue_by_year = {
        year: benchmark_receipts_bn(year, actual_rate_full[year])
        for year in range(earliest_year, last_year + 1)
    }
    revenue_2010_2029 = pd.DataFrame(
        [
            {
                "year": year,
                "fiscal_year": f"{year}-{(year + 1) % 100:02d}",
                "source": "HMRC out-turn"
                if year in hmrc_bn
                else "OBR March 2026 forecast",
                "actual_rate_p_per_litre": round(actual_rate_full[year] * 100, 4),
                "counterfactual_rate_p_per_litre": round(
                    counterfactual_rate_full[year] * 100, 4
                ),
                "actual_revenue_gbp_bn": round(revenue_by_year[year], 4),
                "counterfactual_revenue_gbp_bn": round(
                    revenue_by_year[year]
                    + rate_gap_cost_bn(
                        year,
                        counterfactual_rate_full[year] - actual_rate_full[year],
                        actual_rate_full[year],
                    ),
                    4,
                ),
            }
            for year in range(earliest_year, last_year + 1)
        ]
    )
    revenue_2010_2029["gap_gbp_bn"] = (
        revenue_2010_2029["counterfactual_revenue_gbp_bn"]
        - revenue_2010_2029["actual_revenue_gbp_bn"]
    ).round(4)

    quartiles, quintiles, deciles = _distributional_cuts(
        baseline_sim=baseline_sim,
        keep_cut_sim=keep_cut_sim,
        year_dist=year_dist,
        aggregate_cost_bn=benchmark_cost_bn(
            year_dist,
            actual_rate[year_dist] - post_cut_rate,
        ),
    )

    headline = {
        "guardian_2026": float(
            guardian_check.loc[
                guardian_check.Year == 2026, "Cost of keeping 5p cut (£bn)"
            ].values[0]
        ),
        "guardian_2027": float(
            guardian_check.loc[
                guardian_check.Year == 2027, "Cost of keeping 5p cut (£bn)"
            ].values[0]
        ),
        "scrap_2026": float(
            scrap_5p.loc[scrap_5p.Year == 2026, "Cost to Treasury (£bn)"].values[0]
        ),
        "scrap_2027": float(
            scrap_5p.loc[scrap_5p.Year == 2027, "Cost to Treasury (£bn)"].values[0]
        ),
        "scrap_2029": float(
            scrap_5p.loc[scrap_5p.Year == 2029, "Cost to Treasury (£bn)"].values[0]
        ),
        "scrap_cumulative": float(scrap_5p["Cost to Treasury (£bn)"].sum()),
        "fleet_cumulative": float(
            revenue_2010_2029.loc[
                (revenue_2010_2029.year >= earliest_year)
                & (revenue_2010_2029.year <= 2026),
                "gap_gbp_bn",
            ].sum()
        ),
        "actual_rate_2026_p": float(actual_rate[2026] * 100),
        "counterfactual_rate_2026_p": float(counterfactual_rate[2026] * 100),
        "baseline_rate_2027_p": float(actual_rate[2027] * 100),
        "revenue_last_year_actual_bn": float(revenue_by_year[last_year]),
        "revenue_last_year_counterfactual_bn": float(
            revenue_by_year[last_year]
            + rate_gap_cost_bn(
                last_year,
                counterfactual_rate_full[last_year] - actual_rate_full[last_year],
                actual_rate_full[last_year],
            )
        ),
        "last_year": last_year,
        "year_dist": year_dist,
        "first_freeze_year": FIRST_FREEZE_YEAR,
    }

    pe_version = _policyengine_version()
    model_id = getattr(uk_latest, "id", "uk_latest")
    try:
        pe_uk_version = _pkg_version("policyengine-uk")
    except PackageNotFoundError:
        pe_uk_version = "unknown"
    dataset_label = (
        os.path.basename(dataset_reference)
        if dataset_path is not None
        else DEFAULT_DATASET_NAME
    )
    citation = (
        f"PolicyEngine ({pe_version}); model {model_id} pinned to "
        f"policyengine-uk {pe_uk_version}; enhanced FRS "
        f"({dataset_label}, "
        f"{DEFAULT_DATASET_REPO}@{DEFAULT_DATASET_REVISION}, "
        f"{DEFAULT_DATASET_METHOD_NOTE}); "
        f"OBR RPI series from {OBR_FORECAST_VINTAGE}"
    )

    return Results(
        data_years=data_years,
        scrap_5p=scrap_5p,
        guardian_check=guardian_check,
        rate_history=rate_history,
        rate_path=rate_path,
        revenue_2010_2029=revenue_2010_2029,
        quartiles=quartiles,
        quintiles=quintiles,
        deciles=deciles,
        headline=headline,
        policyengine_version=pe_version,
        citation=citation,
    )


def _find_cut_date(fuel_duty_param) -> str:
    """Locate the 5p-cut date from the parameter history."""
    pairs = sorted(
        ((value.instant_str, value.value) for value in fuel_duty_param.values_list),
        key=lambda pair: pair[0],
    )
    cut_date, cut_drop = None, 0.0
    for (_prev_date, prev_value), (date, value) in zip(pairs, pairs[1:]):
        drop = prev_value - value
        if drop > cut_drop:
            cut_date, cut_drop = date, drop
    return cut_date


def _distributional_cuts(
    *,
    baseline_sim,
    keep_cut_sim,
    year_dist: int,
    aggregate_cost_bn: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Quartile / quintile / decile cuts excluding bottom 5%."""
    fd_base_hh = baseline_sim.calculate("fuel_duty", year_dist)
    fd_keep_hh = keep_cut_sim.calculate("fuel_duty", year_dist)
    raw_cost_bn = (fd_base_hh.sum() - fd_keep_hh.sum()) / 1e9
    scale = aggregate_cost_bn / raw_cost_bn if raw_cost_bn else 1.0

    fd_base = baseline_sim.calculate("fuel_duty", year_dist, map_to="person")
    fd_keep = keep_cut_sim.calculate("fuel_duty", year_dist, map_to="person")
    net_income = baseline_sim.calculate(
        "household_net_income", year_dist, map_to="person"
    )
    equiv = baseline_sim.calculate(
        "equiv_hbai_household_net_income", year_dist, map_to="person"
    )

    saving = (fd_base - fd_keep) * scale
    ranks = equiv.percentile_rank()
    keep_mask = (ranks > 5) & (equiv > 0)
    remaining = (ranks[keep_mask] - 5) / 95 * 100

    def build(div_pct: float, n: int, prefix: str) -> pd.DataFrame:
        idx = pd.Series(
            np.minimum(np.ceil(remaining.values / div_pct).astype(int), n),
            index=remaining.index,
        )
        saving_by_group = saving[keep_mask].groupby(idx).mean()
        income_by_group = net_income[keep_mask].groupby(idx).mean()
        rows = []
        for group in range(1, n + 1):
            saving_value = saving_by_group[group]
            income_value = income_by_group[group]
            rows.append(
                {
                    "group": f"{prefix}{group}",
                    "avg_saving_gbp_per_year": round(saving_value, 2),
                    "avg_net_income_gbp": round(income_value, 2),
                    "saving_pct_of_net_income": round(
                        100 * saving_value / income_value, 3
                    ),
                }
            )
        return pd.DataFrame(rows)

    return build(25, 4, "Q"), build(20, 5, "Q"), build(10, 10, "D")
