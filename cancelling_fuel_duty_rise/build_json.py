"""Build a dashboard-ready JSON snapshot of the analysis."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .simulation import compute_all

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "results" / "fuel_duty_results.json"
DASHBOARD_DATA = (
    Path(__file__).resolve().parents[1] / "dashboard" / "public" / "data" / "fuel_duty_results.json"
)


def _records(df) -> list[dict]:
    """DataFrame → list[dict] with JSON-friendly column names preserved."""
    return df.to_dict(orient="records")


def _payload() -> dict:
    r = compute_all()
    h = r.headline

    return {
        "schema_version": 1,
        "policy_id": "cancelling_fuel_duty_rise",
        "title": "Cancelling the planned fuel duty rise",
        "description": (
            "PolicyEngine UK analysis of the cost, counterfactual, and distributional "
            "impact of cancelling the Autumn Budget 2025 fuel-duty plan."
        ),
        "data_years": r.data_years,
        "year_dist": h["year_dist"],
        "first_freeze_year": h["first_freeze_year"],
        "last_year": h["last_year"],
        "model_versions": {
            "policyengine": r.policyengine_version,
        },
        "citation": r.citation,
        "method_note": r.method_note,
        "headline": h,
        "tables": {
            "scrap_5p_cost": _records(r.scrap_5p),
            "guardian_check": _records(r.guardian_check),
            "litre_check": _records(r.litre_check),
            "rate_history": _records(r.rate_history),
            "rate_path": _records(r.rate_path),
            "revenue_2010_2029": _records(r.revenue_2010_2029),
        },
        "distribution": {
            "default_year": h["year_dist"],
            "years": r.distribution_years,
            "deciles": _records(r.deciles),
            "quintiles": _records(r.quintiles),
            "quartiles": _records(r.quartiles),
            "deciles_by_year": {
                str(y): _records(df) for y, df in r.deciles_by_year.items()
            },
            "quintiles_by_year": {
                str(y): _records(df) for y, df in r.quintiles_by_year.items()
            },
            "quartiles_by_year": {
                str(y): _records(df) for y, df in r.quartiles_by_year.items()
            },
        },
    }


def build(output: Path | str = DEFAULT_OUTPUT, sync_dashboard: bool = False) -> Path:
    """Write the dashboard JSON and optionally copy it into dashboard/public/data."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = _payload()
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    if sync_dashboard:
        DASHBOARD_DATA.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output, DASHBOARD_DATA)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Path to write the JSON snapshot (default: results/fuel_duty_results.json).",
    )
    parser.add_argument(
        "--sync-dashboard",
        action="store_true",
        help="Also copy the JSON to dashboard/public/data/fuel_duty_results.json.",
    )
    args = parser.parse_args()
    path = build(args.output, sync_dashboard=args.sync_dashboard)
    print(f"Wrote {path}")
    if args.sync_dashboard:
        print(f"Synced to {DASHBOARD_DATA}")


if __name__ == "__main__":
    main()
