"""Run the PolicyEngine UK simulations behind the briefing.

Everything downstream (charts, tables, build scripts) consumes the artefacts
produced by :func:`compute_all`. The simulation is expensive so results are
memoised per process.

Design notes
------------
- The simulation entry point is the unified ``policyengine`` package via
  :func:`policyengine.tax_benefit_models.uk.managed_microsimulation`; the
  active UK model and dataset are resolved by the installed ``policyengine.py``
  managed bundle.
- Fiscal totals are benchmarked to HMRC/OBR road-fuel litre controls. The
  PolicyEngine microsimulation provides calibrated household fuel litres for
  distributional allocation.
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
DEFAULT_ANALYSIS_YEARS = list(range(2023, 2030))
ITV_METHOD_NOTE = (
    "PolicyEngine.py provides the household microsimulation and calibrated "
    "petrol and diesel litre distribution. Headline fiscal totals use HMRC/OBR "
    "road-fuel clearances and receipts; distributional savings are household "
    "litres times the relevant duty-rate gap, without post-hoc scaling."
)


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
    litre_check: pd.DataFrame
    quartiles: pd.DataFrame
    quintiles: pd.DataFrame
    deciles: pd.DataFrame
    headline: dict
    policyengine_version: str
    citation: str
    method_note: str


@functools.lru_cache(maxsize=1)
def compute_all(
    dataset_path: str | None = None,
    year_dist: int = 2027,
    hf_token: str | None = None,
) -> Results:
    """Run all simulations once and return the bundled :class:`Results`."""
    if hf_token:
        os.environ["HUGGING_FACE_TOKEN"] = hf_token

    from policyengine.tax_benefit_models.uk import managed_microsimulation

    dataset_reference = dataset_path or DEFAULT_DATASET_NAME
    data_years = (
        _dataset_years(dataset_reference)
        if dataset_path is not None
        else DEFAULT_ANALYSIS_YEARS
    )
    last_year = max(data_years)

    def _sim():
        return managed_microsimulation(
            dataset=dataset_reference,
            allow_unmanaged="://" in dataset_reference,
        )

    baseline_sim = _sim()
    bundle = getattr(baseline_sim, "policyengine_bundle", {}) or {}
    params = baseline_sim.tax_benefit_system.parameters
    fuel_duty = params.gov.hmrc.fuel_duty.petrol_and_diesel
    rpi = params.gov.economic_assumptions.yoy_growth.obr.rpi

    pre_cut_rate = fuel_duty(f"{FIRST_FREEZE_YEAR}-04-01")
    post_cut_rate = fuel_duty(_find_cut_date(fuel_duty))

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

    litre_check = _fuel_litre_check(
        baseline_sim=baseline_sim,
        data_years=data_years,
        actual_rate=actual_rate,
        post_cut_rate=post_cut_rate,
        road_fuel_years=road_fuel_years,
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
        year_dist=year_dist,
        duty_rate_gap=actual_rate[year_dist] - post_cut_rate,
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
        "model_road_fuel_litres_2027_bn": float(
            litre_check.loc[
                litre_check.Year == 2027, "PolicyEngine litres (bn)"
            ].values[0]
        ),
        "benchmark_road_fuel_litres_2027_bn": float(
            litre_check.loc[litre_check.Year == 2027, "HMRC/OBR litres (bn)"].values[0]
        ),
        "model_full_plan_cost_2027_bn": float(
            litre_check.loc[litre_check.Year == 2027, "PolicyEngine cost (£bn)"].values[
                0
            ]
        ),
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
    bundle_policyengine_version = bundle.get("policyengine_version") or pe_version
    citation = (
        f"PolicyEngine.py {bundle_policyengine_version}; "
        f"OBR RPI series from {OBR_FORECAST_VINTAGE}"
    )

    return Results(
        data_years=data_years,
        scrap_5p=scrap_5p,
        guardian_check=guardian_check,
        rate_history=rate_history,
        rate_path=rate_path,
        revenue_2010_2029=revenue_2010_2029,
        litre_check=litre_check,
        quartiles=quartiles,
        quintiles=quintiles,
        deciles=deciles,
        headline=headline,
        policyengine_version=pe_version,
        citation=citation,
        method_note=ITV_METHOD_NOTE,
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


def _fuel_litre_check(
    *,
    baseline_sim,
    data_years: list[int],
    actual_rate: dict[int, float],
    post_cut_rate: float,
    road_fuel_years: dict[int, float],
) -> pd.DataFrame:
    """Compare calibrated PolicyEngine litres with the HMRC/OBR control."""
    rows = []
    for year in data_years:
        pe_litres = baseline_sim.calculate(
            "petrol_litres", year
        ) + baseline_sim.calculate("diesel_litres", year)
        pe_litres_bn = pe_litres.sum() / 1e9
        benchmark_litres_bn = road_fuel_years[year] / 1_000
        rate_gap = actual_rate[year] - post_cut_rate
        rows.append(
            {
                "Year": year,
                "PolicyEngine litres (bn)": round(pe_litres_bn, 4),
                "HMRC/OBR litres (bn)": round(benchmark_litres_bn, 4),
                "PolicyEngine / HMRC-OBR": round(pe_litres_bn / benchmark_litres_bn, 4),
                "Duty-rate gap (p/L)": round(rate_gap * 100, 4),
                "PolicyEngine cost (£bn)": round(pe_litres_bn * rate_gap, 4),
                "HMRC/OBR cost (£bn)": round(benchmark_litres_bn * rate_gap, 4),
            }
        )
    return pd.DataFrame(rows)


def _distributional_cuts(
    *,
    baseline_sim,
    year_dist: int,
    duty_rate_gap: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Quartile / quintile / decile cuts over the full income distribution."""
    petrol_litres = baseline_sim.calculate("petrol_litres", year_dist, map_to="person")
    diesel_litres = baseline_sim.calculate("diesel_litres", year_dist, map_to="person")
    net_income = baseline_sim.calculate(
        "household_net_income", year_dist, map_to="person"
    )
    equiv = baseline_sim.calculate(
        "equiv_hbai_household_net_income", year_dist, map_to="person"
    )

    saving = (petrol_litres + diesel_litres) * duty_rate_gap
    ranks = equiv.percentile_rank()

    def build(div_pct: float, n: int, prefix: str) -> pd.DataFrame:
        idx = pd.Series(
            np.minimum(np.ceil(ranks / div_pct).astype(int), n),
            index=ranks.index,
        )
        saving_by_group = saving.groupby(idx).mean()
        income_by_group = net_income.groupby(idx).mean()
        winners_by_group = (saving > 0).groupby(idx).mean() * 100
        rows = []
        for group in range(1, n + 1):
            saving_value = saving_by_group[group]
            income_value = income_by_group[group]
            pct_winners = float(winners_by_group[group])
            rows.append(
                {
                    "group": f"{prefix}{group}",
                    "avg_saving_gbp_per_year": round(saving_value, 2),
                    "avg_net_income_gbp": round(income_value, 2),
                    "saving_pct_of_net_income": round(
                        100 * saving_value / income_value, 3
                    ),
                    "pct_winners": round(pct_winners, 2),
                    "pct_unchanged": round(100 - pct_winners, 2),
                }
            )
        return pd.DataFrame(rows)

    return build(25, 4, "Q"), build(20, 5, "Q"), build(10, 10, "D")
