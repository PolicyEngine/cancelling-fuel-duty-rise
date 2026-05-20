"""Load PolicyEngine UK data and run all three reform simulations.

Everything downstream (charts, tables, build scripts) consumes the artefacts
produced by :func:`compute_all`. Running PolicyEngine UK is expensive, so the
result is memoised per process.
"""

from __future__ import annotations

import functools
import os
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .volumes import hmrc_receipts_bn

DEFAULT_STORAGE = "/Users/janansadeqian/policyengine-uk-data/policyengine_uk_data/storage/"


@dataclass
class Results:
    """All numbers needed to draw the report.

    Attributes
    ----------
    data_years
        Years covered by the enhanced FRS multi-year dataset.
    scrap_5p
        Per-year cost of cancelling the planned 5p reversal (vs Autumn Budget
        2025 schedule).
    guardian_check
        Per-year cost of keeping 52.95p instead of returning to 57.95p (no
        further RPI uprating) — the Guardian / Fleet News framing.
    rate_history
        Every dated rate value from the PE-UK ``gov.hmrc.fuel_duty`` parameter.
    rate_path
        Actual vs RPI-counterfactual rate from 2011 to the last data year.
    revenue_2010_2029
        OBR-style chart data: HMRC out-turn (2010-2024) + PE-UK projection
        (2025+) + RPI counterfactual revenue + gap.
    quartiles / quintiles / deciles
        Distributional impact in 2027, bottom 5% excluded.
    headline
        Scalar headline numbers for KPI cards.
    """

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


@functools.lru_cache(maxsize=1)
def compute_all(
    dataset_path: str | None = None,
    year_dist: int = 2027,
    hf_token: str | None = None,
) -> Results:
    """Run all three simulations once and return the bundled results."""
    if hf_token:
        os.environ["HUGGING_FACE_TOKEN"] = hf_token

    from microdf import MicroSeries
    from policyengine_uk import Microsimulation
    from policyengine_uk.data import UKMultiYearDataset
    from policyengine_uk_data.utils.huggingface import download

    storage = os.path.dirname(dataset_path) if dataset_path else DEFAULT_STORAGE
    if dataset_path is None:
        dataset_path = download(
            "policyengine/policyengine-uk-data",
            "enhanced_frs_2023_29.h5",
            storage,
        )

    dataset = UKMultiYearDataset(file_path=dataset_path)
    data_years = list(dataset.years)
    first_year, last_year = min(data_years), max(data_years)

    baseline_sim = Microsimulation(dataset=dataset)
    params = baseline_sim.tax_benefit_system.parameters
    fuel_duty_param = params.gov.hmrc.fuel_duty.petrol_and_diesel
    rpi_param = params.gov.economic_assumptions.yoy_growth.obr.rpi

    POST_CUT_RATE = fuel_duty_param("2022-04-01")
    PRE_CUT_RATE = fuel_duty_param("2011-04-01")

    keep_cut_sim = Microsimulation(
        dataset=dataset,
        reform={
            "gov.hmrc.fuel_duty.petrol_and_diesel": {
                f"{first_year}-01-01.{last_year}-12-31": POST_CUT_RATE,
            }
        },
    )
    just_reversal_sim = Microsimulation(
        dataset=dataset,
        reform={
            "gov.hmrc.fuel_duty.petrol_and_diesel": {
                f"{first_year}-01-01.{last_year}-12-31": PRE_CUT_RATE,
            }
        },
    )

    FIRST_FREEZE_YEAR = 2011
    counterfactual_rate = {FIRST_FREEZE_YEAR: PRE_CUT_RATE}
    for y in range(FIRST_FREEZE_YEAR + 1, last_year + 1):
        counterfactual_rate[y] = counterfactual_rate[y - 1] * (
            1 + rpi_param(f"{y}-01-01")
        )
    actual_rate = {
        y: fuel_duty_param(f"{y}-06-01")
        for y in range(FIRST_FREEZE_YEAR, last_year + 1)
    }

    rpi_sim = Microsimulation(
        dataset=dataset,
        reform={
            "gov.hmrc.fuel_duty.petrol_and_diesel": {
                f"{y}-01-01.{y}-12-31": counterfactual_rate[y] for y in data_years
            }
        },
    )

    # ---- table: cost of cancelling the planned 5p reversal ----
    scrap_5p = pd.DataFrame(
        [
            {
                "Year": y,
                "Baseline rate (p/L)": round(fuel_duty_param(f"{y}-06-01") * 100, 2),
                "Baseline revenue (£bn)": round(
                    baseline_sim.calculate("fuel_duty", y).sum() / 1e9, 2
                ),
                "Reform revenue (£bn)": round(
                    keep_cut_sim.calculate("fuel_duty", y).sum() / 1e9, 2
                ),
                "Cost to Treasury (£bn)": round(
                    (
                        baseline_sim.calculate("fuel_duty", y).sum()
                        - keep_cut_sim.calculate("fuel_duty", y).sum()
                    )
                    / 1e9,
                    2,
                ),
            }
            for y in data_years
        ]
    )

    # ---- table: Guardian-framing 5p-only cost ----
    guardian_check = pd.DataFrame(
        [
            {
                "Year": y,
                "Revenue at 52.95p (£bn)": round(
                    keep_cut_sim.calculate("fuel_duty", y).sum() / 1e9, 2
                ),
                "Revenue at 57.95p (£bn)": round(
                    just_reversal_sim.calculate("fuel_duty", y).sum() / 1e9, 2
                ),
                "Cost of keeping 5p cut (£bn)": round(
                    (
                        just_reversal_sim.calculate("fuel_duty", y).sum()
                        - keep_cut_sim.calculate("fuel_duty", y).sum()
                    )
                    / 1e9,
                    2,
                ),
            }
            for y in data_years
        ]
    )

    # ---- table: rate history ----
    rate_history = (
        pd.DataFrame(
            [
                {
                    "date": v.instant_str,
                    "rate_per_litre_gbp": v.value,
                    "rate_pence_per_litre": round(v.value * 100, 4),
                }
                for v in fuel_duty_param.values_list
            ]
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    # ---- table: rate path 2011-2029 ----
    rate_path = pd.DataFrame(
        [
            {
                "year": y,
                "rpi_yoy_growth_pct": round(rpi_param(f"{y}-01-01") * 100, 4),
                "actual_rate_p_per_litre": round(actual_rate[y] * 100, 4),
                "rpi_counterfactual_rate_p_per_litre": round(
                    counterfactual_rate[y] * 100, 4
                ),
                "gap_p_per_litre": round(
                    (counterfactual_rate[y] - actual_rate[y]) * 100, 4
                ),
            }
            for y in sorted(counterfactual_rate.keys())
        ]
    )

    # ---- table: 2010-2029 revenue series ----
    hmrc_bn = hmrc_receipts_bn()
    pe_uk_projection = {
        y: baseline_sim.calculate("fuel_duty", y).sum() / 1e9 for y in data_years
    }
    revenue_by_year = {
        y: (hmrc_bn[y] if y in hmrc_bn else pe_uk_projection[y])
        for y in range(2010, last_year + 1)
    }
    counterfactual_rate_full = {2010: fuel_duty_param("2010-04-01")}
    for y in range(2011, last_year + 1):
        counterfactual_rate_full[y] = counterfactual_rate_full[y - 1] * (
            1 + rpi_param(f"{y}-01-01")
        )
    actual_rate_full = {
        y: fuel_duty_param(f"{y}-06-01") for y in range(2010, last_year + 1)
    }
    revenue_2010_2029 = pd.DataFrame(
        [
            {
                "year": y,
                "fiscal_year": f"{y}-{(y + 1) % 100:02d}",
                "source": "HMRC out-turn"
                if y in hmrc_bn
                else "PolicyEngine UK projection",
                "actual_rate_p_per_litre": round(actual_rate_full[y] * 100, 4),
                "counterfactual_rate_p_per_litre": round(
                    counterfactual_rate_full[y] * 100, 4
                ),
                "actual_revenue_gbp_bn": round(revenue_by_year[y], 4),
                "counterfactual_revenue_gbp_bn": round(
                    revenue_by_year[y]
                    * counterfactual_rate_full[y]
                    / actual_rate_full[y],
                    4,
                ),
            }
            for y in range(2010, last_year + 1)
        ]
    )
    revenue_2010_2029["gap_gbp_bn"] = (
        revenue_2010_2029["counterfactual_revenue_gbp_bn"]
        - revenue_2010_2029["actual_revenue_gbp_bn"]
    ).round(4)

    # ---- distributional cuts ----
    quartiles, quintiles, deciles = _distributional_cuts(
        baseline_sim=baseline_sim,
        keep_cut_sim=keep_cut_sim,
        year_dist=year_dist,
    )

    # ---- headline scalars ----
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
                (revenue_2010_2029.year >= 2010)
                & (revenue_2010_2029.year <= 2026),
                "gap_gbp_bn",
            ].sum()
        ),
        "actual_rate_2026_p": float(actual_rate[2026] * 100),
        "counterfactual_rate_2026_p": float(counterfactual_rate[2026] * 100),
        "revenue_last_year_actual_bn": float(revenue_by_year[last_year]),
        "revenue_last_year_counterfactual_bn": float(
            revenue_by_year[last_year]
            * counterfactual_rate_full[last_year]
            / actual_rate_full[last_year]
        ),
        "last_year": last_year,
        "year_dist": year_dist,
    }

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
    )


def _distributional_cuts(
    *,
    baseline_sim,
    keep_cut_sim,
    year_dist: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Quartile / quintile / decile cuts excluding bottom 5%."""
    from microdf import MicroSeries

    fd_base = baseline_sim.calculate("fuel_duty", year_dist)
    fd_keep = keep_cut_sim.calculate("fuel_duty", year_dist)
    net_income = baseline_sim.calculate("household_net_income", year_dist)
    equiv = baseline_sim.calculate(
        "equiv_hbai_household_net_income", year_dist
    ).values
    hh_size = baseline_sim.calculate("household_count_people", year_dist).values
    wgt = baseline_sim.calculate("household_weight", year_dist).values

    person_w = wgt * hh_size
    saving_arr = (fd_base - fd_keep).values
    net_inc_arr = net_income.values

    ranks = MicroSeries(equiv, weights=person_w).percentile_rank().values
    keep_mask = (ranks > 5) & (equiv > 0)
    remaining = (ranks[keep_mask] - 5) / 95 * 100

    def build(div_pct: float, n: int, prefix: str) -> pd.DataFrame:
        idx = np.minimum(np.ceil(remaining / div_pct).astype(int), n)
        rows = []
        for g in range(1, n + 1):
            m = idx == g
            s = (saving_arr[keep_mask][m] * person_w[keep_mask][m]).sum() / person_w[
                keep_mask
            ][m].sum()
            inc = (net_inc_arr[keep_mask][m] * person_w[keep_mask][m]).sum() / person_w[
                keep_mask
            ][m].sum()
            rows.append(
                {
                    "group": f"{prefix}{g}",
                    "avg_saving_gbp_per_year": round(s, 2),
                    "avg_net_income_gbp": round(inc, 2),
                    "saving_pct_of_net_income": round(100 * s / inc, 3),
                }
            )
        return pd.DataFrame(rows)

    return build(25, 4, "Q"), build(20, 5, "Q"), build(10, 10, "D")
