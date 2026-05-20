"""Run the PolicyEngine UK simulations behind the briefing.

Everything downstream (charts, tables, build scripts) consumes the artefacts
produced by :func:`compute_all`. The simulation is expensive so results are
memoised per process.

Design notes
------------
- The simulation entry point is the unified ``policyengine`` package via
  :func:`policyengine.tax_benefit_models.uk.managed_microsimulation`. The
  version stamped onto each output comes from ``policyengine.__version__``.
- All rate and macro parameters (fuel-duty rate history, OBR RPI series,
  pump prices) come from the PolicyEngine UK parameter tree. The only
  numerically-fixed values in the code are dates of policy events
  (e.g. 2011 first freeze, 2022 5p cut) which are documented historical
  anchors, plus HMRC's published fuel-duty receipts series in
  :mod:`cancelling_fuel_duty_rise.historical`.
- All weighted aggregates use the native ``microdf`` :class:`MicroSeries`
  API (``.sum()``, ``.mean()``, ``.groupby(...).mean()``). The package
  never multiplies values by weights by hand.
"""

from __future__ import annotations

import functools
import os
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .historical import (
    FIRST_FREEZE_YEAR,
    OBR_FORECAST_VINTAGE,
    hmrc_receipts_bn,
)

DEFAULT_DATASET_FILENAME = "enhanced_frs_2023_29.h5"
DEFAULT_DATASET_REPO = "policyengine/policyengine-uk-data"


def _default_storage_dir() -> str:
    """Pick a writable cache directory for downloaded datasets.

    Order of preference:
      1. ``$CANCELLING_FUEL_DUTY_RISE_DATA_DIR`` if set
      2. ``$XDG_CACHE_HOME/cancelling-fuel-duty-rise`` (Linux default)
      3. ``~/.cache/cancelling-fuel-duty-rise``
    """
    custom = os.environ.get("CANCELLING_FUEL_DUTY_RISE_DATA_DIR")
    if custom:
        return os.path.expanduser(custom)
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = xdg if xdg else os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(base, "cancelling-fuel-duty-rise")


def _policyengine_version() -> str:
    """Return the installed ``policyengine`` Python package version.

    Reads the installed distribution metadata directly so that obtaining the
    version does not require importing ``policyengine`` (which transitively
    loads the US and UK tax-benefit models).
    """
    from importlib.metadata import version

    return version("policyengine")


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
        Every dated rate value from the ``gov.hmrc.fuel_duty`` parameter.
    rate_path
        Actual vs RPI-counterfactual rate from the first freeze year to the
        last data year.
    revenue_2010_2029
        OBR-style chart data: HMRC out-turn (pre-2025) + PolicyEngine UK
        projection (2025+) + RPI counterfactual revenue + gap.
    quartiles / quintiles / deciles
        Distributional impact in ``year_dist``, bottom 5% by equivalised
        income excluded (Resolution Foundation convention).
    headline
        Scalar headline numbers for KPI cards.
    policyengine_version
        Version string of the ``policyengine`` package used to build the run.
    citation
        One-line citation describing the model and dataset bundle.
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

    from microdf import MicroSeries
    from policyengine.tax_benefit_models.uk import (
        managed_microsimulation,
        uk_latest,
    )
    from policyengine_uk_data.utils.huggingface import download

    if dataset_path is None:
        storage = _default_storage_dir()
        os.makedirs(storage, exist_ok=True)
        dataset_path = download(
            DEFAULT_DATASET_REPO,
            DEFAULT_DATASET_FILENAME,
            storage,
        )

    def _sim(*, reform: dict | None = None):
        """policyengine.py-managed Microsimulation for this dataset."""
        kwargs = {"reform": reform} if reform is not None else {}
        return managed_microsimulation(
            dataset=dataset_path,
            allow_unmanaged=True,
            **kwargs,
        )

    baseline_sim = _sim()
    data_years = sorted(int(y) for y in baseline_sim.dataset.years)
    first_year, last_year = min(data_years), max(data_years)

    params = baseline_sim.tax_benefit_system.parameters
    fuel_duty = params.gov.hmrc.fuel_duty.petrol_and_diesel
    rpi = params.gov.economic_assumptions.yoy_growth.obr.rpi

    # All rates and dates here are read from the PolicyEngine UK parameter
    # tree: nothing about the 5p cut or the pre-cut headline rate is
    # baked into this code.
    pre_cut_rate = fuel_duty(f"{FIRST_FREEZE_YEAR}-04-01")  # 57.95p
    post_cut_rate = fuel_duty(_find_cut_date(fuel_duty))  # 52.95p

    reform_window = f"{first_year}-01-01.{last_year}-12-31"

    keep_cut_sim = _sim(
        reform={
            "gov.hmrc.fuel_duty.petrol_and_diesel": {reform_window: post_cut_rate}
        },
    )
    just_reversal_sim = _sim(
        reform={
            "gov.hmrc.fuel_duty.petrol_and_diesel": {reform_window: pre_cut_rate}
        },
    )

    # RPI counterfactual rate path, compounded from the first freeze
    # using the OBR RPI series held in PE-UK.
    counterfactual_rate = {FIRST_FREEZE_YEAR: pre_cut_rate}
    for y in range(FIRST_FREEZE_YEAR + 1, last_year + 1):
        counterfactual_rate[y] = counterfactual_rate[y - 1] * (
            1 + rpi(f"{y}-01-01")
        )
    actual_rate = {
        y: fuel_duty(f"{y}-06-01")
        for y in range(FIRST_FREEZE_YEAR, last_year + 1)
    }

    rpi_sim = _sim(
        reform={
            "gov.hmrc.fuel_duty.petrol_and_diesel": {
                f"{y}-01-01.{y}-12-31": counterfactual_rate[y] for y in data_years
            }
        },
    )

    # ---- weighted revenue series via native MicroSeries.sum() ----
    fd_base_year = {
        y: baseline_sim.calculate("fuel_duty", y) for y in data_years
    }
    fd_keep_year = {
        y: keep_cut_sim.calculate("fuel_duty", y) for y in data_years
    }
    fd_reversal_year = {
        y: just_reversal_sim.calculate("fuel_duty", y) for y in data_years
    }

    scrap_5p = pd.DataFrame(
        [
            {
                "Year": y,
                "Baseline rate (p/L)": round(fuel_duty(f"{y}-06-01") * 100, 2),
                "Baseline revenue (£bn)": round(fd_base_year[y].sum() / 1e9, 2),
                "Reform revenue (£bn)": round(fd_keep_year[y].sum() / 1e9, 2),
                "Cost to Treasury (£bn)": round(
                    (fd_base_year[y].sum() - fd_keep_year[y].sum()) / 1e9, 2
                ),
            }
            for y in data_years
        ]
    )

    guardian_check = pd.DataFrame(
        [
            {
                "Year": y,
                "Revenue at 52.95p (£bn)": round(
                    fd_keep_year[y].sum() / 1e9, 2
                ),
                "Revenue at 57.95p (£bn)": round(
                    fd_reversal_year[y].sum() / 1e9, 2
                ),
                "Cost of keeping 5p cut (£bn)": round(
                    (fd_reversal_year[y].sum() - fd_keep_year[y].sum()) / 1e9, 2
                ),
            }
            for y in data_years
        ]
    )

    rate_history = (
        pd.DataFrame(
            [
                {
                    "date": v.instant_str,
                    "rate_per_litre_gbp": v.value,
                    "rate_pence_per_litre": round(v.value * 100, 4),
                }
                for v in fuel_duty.values_list
            ]
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    rate_path = pd.DataFrame(
        [
            {
                "year": y,
                "rpi_yoy_growth_pct": round(rpi(f"{y}-01-01") * 100, 4),
                "actual_rate_p_per_litre": round(actual_rate[y] * 100, 4),
                "rpi_counterfactual_rate_p_per_litre": round(
                    counterfactual_rate[y] * 100, 4
                ),
                "gap_p_per_litre": round(
                    (counterfactual_rate[y] - actual_rate[y]) * 100, 4
                ),
            }
            for y in sorted(counterfactual_rate)
        ]
    )

    # ---- 2010-2029 revenue series: HMRC out-turn + PE-UK forecast ----
    hmrc_bn = hmrc_receipts_bn()
    earliest_year = min(hmrc_bn)  # 2010 from HMRC table
    pe_uk_projection = {y: fd_base_year[y].sum() / 1e9 for y in data_years}
    revenue_by_year = {
        y: (hmrc_bn[y] if y in hmrc_bn else pe_uk_projection[y])
        for y in range(earliest_year, last_year + 1)
    }
    counterfactual_rate_full = {earliest_year: fuel_duty(f"{earliest_year}-04-01")}
    for y in range(earliest_year + 1, last_year + 1):
        counterfactual_rate_full[y] = counterfactual_rate_full[y - 1] * (
            1 + rpi(f"{y}-01-01")
        )
    actual_rate_full = {
        y: fuel_duty(f"{y}-06-01") for y in range(earliest_year, last_year + 1)
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
            for y in range(earliest_year, last_year + 1)
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
    last_outturn_year = max(hmrc_bn)
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
        "revenue_last_year_actual_bn": float(revenue_by_year[last_year]),
        "revenue_last_year_counterfactual_bn": float(
            revenue_by_year[last_year]
            * counterfactual_rate_full[last_year]
            / actual_rate_full[last_year]
        ),
        "last_year": last_year,
        "last_outturn_year": last_outturn_year,
        "year_dist": year_dist,
        "first_freeze_year": FIRST_FREEZE_YEAR,
    }

    pe_version = _policyengine_version()
    citation = (
        f"PolicyEngine ({pe_version}); model {uk_latest.id} pinned to "
        f"policyengine-uk {uk_latest.country_version}; dataset "
        f"{os.path.basename(dataset_path)}; OBR RPI series from "
        f"{OBR_FORECAST_VINTAGE}"
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
    """Locate the 5p-cut date from the parameter history.

    The 5p cut is the largest single year-on-year *decrease* in the rate.
    Discovering it from the parameter file avoids hard-coding the 2022-03-23
    date and keeps the code robust to future parameter edits.
    """
    pairs = sorted(
        ((v.instant_str, v.value) for v in fuel_duty_param.values_list),
        key=lambda p: p[0],
    )
    cut_date, cut_drop = None, 0.0
    for (d_prev, v_prev), (d_curr, v_curr) in zip(pairs, pairs[1:]):
        drop = v_prev - v_curr
        if drop > cut_drop:
            cut_date, cut_drop = d_curr, drop
    return cut_date


def _distributional_cuts(
    *,
    baseline_sim,
    keep_cut_sim,
    year_dist: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Per-decile / quintile / quartile saving from keeping the 5p cut.

    Uses the Resolution Foundation convention of excluding the bottom 5% by
    equivalised income before splitting the remaining 95% into groups.

    All weighted aggregates use ``microdf.MicroSeries`` natively: the
    function never multiplies values by weights by hand.
    """
    from microdf import MicroSeries

    fd_base = baseline_sim.calculate("fuel_duty", year_dist)
    fd_keep = keep_cut_sim.calculate("fuel_duty", year_dist)
    net_income = baseline_sim.calculate("household_net_income", year_dist)
    equiv = baseline_sim.calculate(
        "equiv_hbai_household_net_income", year_dist
    )
    hh_size = baseline_sim.calculate("household_count_people", year_dist)

    # Person-weighted equivalised income (HBAI convention) — used to rank.
    person_weights = equiv.weights * hh_size.values
    equiv_ps = MicroSeries(equiv.values, weights=person_weights)
    saving_ps = MicroSeries(fd_base.values - fd_keep.values, weights=person_weights)
    net_inc_ps = MicroSeries(net_income.values, weights=person_weights)

    # Person-weighted percentile rank; drop the bottom 5% and any
    # non-positive equivalised income.
    ranks = equiv_ps.percentile_rank().values
    keep = (ranks > 5) & (equiv.values > 0)

    # Re-rank within the retained 95% and subset to MicroSeries on that mask.
    equiv_kept = MicroSeries(equiv.values[keep], weights=person_weights[keep])
    rank_within = equiv_kept.percentile_rank().values
    saving_kept = MicroSeries(saving_ps.values[keep], weights=person_weights[keep])
    inc_kept = MicroSeries(net_inc_ps.values[keep], weights=person_weights[keep])

    def build(n_groups: int, prefix: str) -> pd.DataFrame:
        bin_width = 100.0 / n_groups
        group_idx = np.minimum(
            np.ceil(rank_within / bin_width).astype(int), n_groups
        )
        labels = np.array([f"{prefix}{g}" for g in group_idx])
        avg_save = saving_kept.groupby(labels).mean()
        avg_inc = inc_kept.groupby(labels).mean()
        return pd.DataFrame(
            [
                {
                    "group": f"{prefix}{g}",
                    "avg_saving_gbp_per_year": round(
                        float(avg_save.loc[f"{prefix}{g}"]), 2
                    ),
                    "avg_net_income_gbp": round(
                        float(avg_inc.loc[f"{prefix}{g}"]), 2
                    ),
                    "saving_pct_of_net_income": round(
                        100
                        * float(avg_save.loc[f"{prefix}{g}"])
                        / float(avg_inc.loc[f"{prefix}{g}"]),
                        3,
                    ),
                }
                for g in range(1, n_groups + 1)
            ]
        )

    return build(4, "Q"), build(5, "Q"), build(10, "D")
