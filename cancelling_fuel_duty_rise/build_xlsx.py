"""Build a multi-sheet Excel workbook with every dataset behind the briefing."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from openpyxl.utils import get_column_letter

from .simulation import compute_all

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "results" / "analysis.xlsx"


def build(output: Path | str = DEFAULT_OUTPUT) -> Path:
    r = compute_all()
    h = r.headline

    # README sheet
    readme = pd.DataFrame(
        [
            ["Sheet", "Description", "Used in chart"],
            [
                "rate_history",
                "Full fuel-duty rate history from PolicyEngine UK parameter gov.hmrc.fuel_duty.petrol_and_diesel",
                "Reference",
            ],
            [
                "rate_path_2011_2029",
                "Annual actual fuel-duty rate vs RPI-uprated counterfactual rate (from 2011)",
                "Chart 'What would the rate be if it had risen with RPI since 2011?'",
            ],
            [
                "scrap_5p_cost",
                "Annual cost of scrapping the planned 5p reversal: baseline = Autumn Budget 2025 schedule; reform = hold 52.95p",
                "Chart 'How much does scrapping the 5p increase cost?'",
            ],
            [
                "guardian_check_5p_only",
                "Cost of keeping 52.95p vs return to 57.95p (no further RPI uprating) — the Guardian framing",
                "Numbers in 'Does this match the Guardian and Fleet News?'",
            ],
            [
                "revenue_2010_2029",
                "OBR-style chart data: HMRC out-turn 2010-11 to 2024-25, OBR receipts forecast from 2025-26, plus RPI counterfactual revenue",
                "Chart 'How much money have the freezes lost so far?'",
            ],
            [
                "litre_check",
                "Year-by-year check of calibrated PolicyEngine road-fuel litres against HMRC/OBR road-fuel controls",
                "Method cross-check",
            ],
            [
                "quartiles_2027",
                "Person-weighted distributional impact 2027 by income quartile, bottom 5% excluded",
                "Chart 'Who gains from keeping the cut?' (quartile cut)",
            ],
            [
                "quintiles_2027",
                "Person-weighted distributional impact 2027 by income quintile, bottom 5% excluded",
                "Chart 'Who gains from keeping the cut?' (quintile cut)",
            ],
            [
                "deciles_2027",
                "Person-weighted distributional impact 2027 by income decile, bottom 5% excluded",
                "Chart 'Who gains from keeping the cut?' (decile cut)",
            ],
            [
                "crosscheck",
                "Cross-check of PolicyEngine UK figures against Guardian and Fleet News numbers",
                "Section 'Does this match...'",
            ],
            ["", "", ""],
            ["Source", "Detail", ""],
            [
                "Distributional household microsim",
                r.citation,
                "",
            ],
            [
                "Method note",
                r.method_note,
                "",
            ],
            [
                "Headline fiscal totals",
                "HMRC road-fuel clearances and UK Tax & NICs receipts; OBR March 2026 fuel-duty receipts forecast",
                "",
            ],
            [
                "Historical receipts",
                "HMRC UK Tax & NICs receipts publication (gov.uk)",
                "",
            ],
            ["RPI series", "OBR Economic and Fiscal Outlook, March 2026", ""],
            [
                "Behavioural responses",
                "None modelled. Fuel volumes held fixed across scenarios.",
                "",
            ],
        ]
    )
    readme.columns = ["", "", ""]

    crosscheck = pd.DataFrame(
        [
            {
                "source": "Guardian (Kiran Stacey, 18 May 2026)",
                "quoted_figure": "£2.4 bn / year",
                "pe_uk_metric": "OBR/HMRC litre benchmark: 52.95p vs return to 57.95p (no RPI uprating)",
                "pe_uk_value_2026_27_gbp_bn": round(h["guardian_2026"], 4),
                "pe_uk_value_2027_28_gbp_bn": round(h["guardian_2027"], 4),
                "url": "https://www.theguardian.com/politics/2026/may/18/rachel-reeves-fuel-duty-cost-of-living",
            },
            {
                "source": "Fleet News (Gareth Roberts, 18 May 2026)",
                "quoted_figure": "~£120 bn cumulative 2010/11 → 2026/27",
                "pe_uk_metric": "Cumulative gap between HMRC/OBR benchmark revenue and RPI counterfactual",
                "pe_uk_value_2026_27_gbp_bn": round(h["fleet_cumulative"], 4),
                "pe_uk_value_2027_28_gbp_bn": None,
                "url": "https://www.fleetnews.co.uk/news/chancellor-expected-to-scrap-5p-fuel-duty-hike",
            },
        ]
    )

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        readme.to_excel(writer, sheet_name="README", index=False, header=False)
        r.rate_history.to_excel(writer, sheet_name="rate_history", index=False)
        r.rate_path.to_excel(writer, sheet_name="rate_path_2011_2029", index=False)
        r.scrap_5p.to_excel(writer, sheet_name="scrap_5p_cost", index=False)
        r.guardian_check.to_excel(
            writer, sheet_name="guardian_check_5p_only", index=False
        )
        r.revenue_2010_2029.to_excel(
            writer, sheet_name="revenue_2010_2029", index=False
        )
        r.litre_check.to_excel(writer, sheet_name="litre_check", index=False)
        r.quartiles.to_excel(writer, sheet_name="quartiles_2027", index=False)
        r.quintiles.to_excel(writer, sheet_name="quintiles_2027", index=False)
        r.deciles.to_excel(writer, sheet_name="deciles_2027", index=False)
        crosscheck.to_excel(writer, sheet_name="crosscheck", index=False)

        for sheet in writer.sheets.values():
            for col in sheet.columns:
                max_len = max(
                    (len(str(c.value)) if c.value is not None else 0) for c in col
                )
                sheet.column_dimensions[get_column_letter(col[0].column)].width = min(
                    max_len + 2, 60
                )

    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT, type=Path)
    args = parser.parse_args()
    path = build(args.output)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
