"""End-to-end pipeline runner.

Runs the PolicyEngine UK simulation once and writes every artefact for the
briefing into ``./results/``:

- ``analysis.html``       — interactive Plotly report
- ``analysis.docx``       — Word document with PNG-rendered charts
- ``analysis.xlsx``       — multi-sheet workbook with every dataset
- ``chart_*.png``         — individual charts as standalone images
- ``table_*.csv``         — individual tables as standalone CSVs

Usage::

    HUGGING_FACE_TOKEN=hf_… uv run python run.py
"""

from __future__ import annotations

from pathlib import Path

from cancelling_fuel_duty_rise import build_docx, build_html, build_xlsx
from cancelling_fuel_duty_rise.charts import (
    annual_cost_chart,
    distributional_chart,
    obr_style_chart,
    rate_path_chart,
)
from cancelling_fuel_duty_rise.simulation import compute_all
from cancelling_fuel_duty_rise.theme import register_template

RESULTS_DIR = Path(__file__).parent / "results"


def _save_png(fig, name: str, w: int = 1100, h: int = 550) -> None:
    fig.write_image(RESULTS_DIR / name, width=w, height=h, scale=2)


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    register_template()

    print("Running PolicyEngine UK simulation (this may take ~1 minute)...")
    r = compute_all()
    print(f"   {r.citation}")

    print("Building HTML report...")
    build_html.build(RESULTS_DIR / "analysis.html")

    print("Building DOCX report...")
    build_docx.build(RESULTS_DIR / "analysis.docx")

    print("Building XLSX workbook...")
    build_xlsx.build(RESULTS_DIR / "analysis.xlsx")

    print("Saving individual charts as PNG...")
    h = r.headline
    _save_png(annual_cost_chart(r.scrap_5p), "chart_annual_cost.png", 900, 460)
    _save_png(rate_path_chart(r.rate_path), "chart_rate_path.png", 950, 520)
    _save_png(obr_style_chart(r.revenue_2010_2029), "chart_obr_style.png", 1100, 600)
    _save_png(
        distributional_chart(
            r.quartiles,
            group_label="Income quartile (Q1 = lowest, Q4 = highest)",
            title=f"Saving from cancelling the planned fuel-duty rise, by quartile (bottom 5% excluded, {h['year_dist']})",
        ),
        "chart_quartiles.png",
        900,
        440,
    )
    _save_png(
        distributional_chart(
            r.quintiles,
            group_label="Income quintile (Q1 = lowest, Q5 = highest)",
            title=f"Saving from cancelling the planned fuel-duty rise, by quintile (bottom 5% excluded, {h['year_dist']})",
        ),
        "chart_quintiles.png",
        900,
        440,
    )
    _save_png(
        distributional_chart(
            r.deciles,
            group_label="Income decile (D1 = next lowest, D10 = highest)",
            title=f"Saving from cancelling the planned fuel-duty rise, by decile (bottom 5% excluded, {h['year_dist']})",
        ),
        "chart_deciles.png",
        900,
        440,
    )

    print("Saving individual tables as CSV...")
    r.scrap_5p.to_csv(RESULTS_DIR / "table_scrap_5p_cost.csv", index=False)
    r.guardian_check.to_csv(RESULTS_DIR / "table_guardian_check.csv", index=False)
    r.litre_check.to_csv(RESULTS_DIR / "table_litre_check.csv", index=False)
    r.rate_history.to_csv(RESULTS_DIR / "table_rate_history.csv", index=False)
    r.rate_path.to_csv(RESULTS_DIR / "table_rate_path.csv", index=False)
    r.revenue_2010_2029.to_csv(RESULTS_DIR / "table_revenue_2010_2029.csv", index=False)
    r.quartiles.to_csv(RESULTS_DIR / "table_quartiles.csv", index=False)
    r.quintiles.to_csv(RESULTS_DIR / "table_quintiles.csv", index=False)
    r.deciles.to_csv(RESULTS_DIR / "table_deciles.csv", index=False)

    print(f"\nDone — all artefacts written to {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
