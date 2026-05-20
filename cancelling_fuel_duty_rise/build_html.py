"""Build the briefing as a standalone HTML file."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from .charts import (
    annual_cost_chart,
    distributional_chart,
    obr_style_chart,
    rate_path_chart,
)
from .simulation import compute_all
from .theme import (
    PE_BLUE,
    PE_FONT,
    PE_GOLD,
    PE_GRAY,
    PE_LIGHT,
    PE_RED,
    PE_TEAL,
    register_template,
)

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "results" / "analysis.html"


def _df_to_html(df: pd.DataFrame) -> str:
    return df.to_html(index=False, border=0, float_format=lambda x: f"{x:,.2f}")


def _fig_to_div(fig: go.Figure, include_js: bool = False) -> str:
    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn" if include_js else False,
        config={"displaylogo": False, "responsive": True},
    )


def build(output: Path | str = DEFAULT_OUTPUT) -> Path:
    register_template()
    r = compute_all()
    h = r.headline

    chart1 = annual_cost_chart(r.scrap_5p)
    chart2 = rate_path_chart(r.rate_path)
    chart3 = obr_style_chart(r.revenue_2010_2029)
    chart_quart = distributional_chart(
        r.quartiles,
        group_label="Income quartile (Q1 = lowest, Q4 = highest)",
        title=f"Saving from cancelling the planned fuel-duty rise, by quartile (bottom 5% excluded, {h['year_dist']})",
    )
    chart_quint = distributional_chart(
        r.quintiles,
        group_label="Income quintile (Q1 = lowest, Q5 = highest)",
        title=f"Saving from cancelling the planned fuel-duty rise, by quintile (bottom 5% excluded, {h['year_dist']})",
    )
    chart_dec = distributional_chart(
        r.deciles,
        group_label="Income decile (D1 = next lowest, D10 = highest)",
        title=f"Saving from cancelling the planned fuel-duty rise, by decile (bottom 5% excluded, {h['year_dist']})",
    )

    css = _CSS_TEMPLATE.format(
        PE_BLUE=PE_BLUE,
        PE_TEAL=PE_TEAL,
        PE_RED=PE_RED,
        PE_GRAY=PE_GRAY,
        PE_LIGHT=PE_LIGHT,
        PE_GOLD=PE_GOLD,
        PE_FONT=PE_FONT,
    )

    html = _HTML_TEMPLATE.format(
        css=css,
        citation=r.citation,
        method_note=r.method_note,
        chart1=_fig_to_div(chart1, include_js=True),
        chart2=_fig_to_div(chart2),
        chart3=_fig_to_div(chart3),
        chart_quart=_fig_to_div(chart_quart),
        chart_quint=_fig_to_div(chart_quint),
        chart_dec=_fig_to_div(chart_dec),
        scrap_5p_table=_df_to_html(r.scrap_5p[r.scrap_5p["Year"] >= 2026]),
        quartiles_table=_df_to_html(r.quartiles),
        quintiles_table=_df_to_html(r.quintiles),
        deciles_table=_df_to_html(r.deciles),
        rate_history_table=_df_to_html(
            r.rate_history[r.rate_history["date"] >= "2010-01-01"].head(25)
        ),
        scrap_2027=h["scrap_2027"],
        guardian_2027=h["guardian_2027"],
        guardian_2026=h["guardian_2026"],
        fleet_cumulative=h["fleet_cumulative"],
        scrap_2029=h["scrap_2029"],
        cumulative=h["scrap_cumulative"],
        actual_rate=h["actual_rate_2026_p"],
        baseline_rate_2027=h["baseline_rate_2027_p"],
        counterfactual_rate=h["counterfactual_rate_2026_p"],
        rate_multiplier=h["counterfactual_rate_2026_p"] / h["actual_rate_2026_p"],
        revenue_actual=h["revenue_last_year_actual_bn"],
        revenue_counterfactual=h["revenue_last_year_counterfactual_bn"],
        revenue_gap=h["revenue_last_year_counterfactual_bn"]
        - h["revenue_last_year_actual_bn"],
        scrap_minus_guardian=h["scrap_2027"] - h["guardian_2027"],
        avg_saving=r.deciles["avg_saving_gbp_per_year"].mean(),
        last_year=h["last_year"],
        last_year_fy=f"{h['last_year']}-{(h['last_year'] + 1) % 100:02d}",
    )

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return output


_CSS_TEMPLATE = """
<style>
  :root {{
    --pe-blue: {PE_BLUE}; --pe-teal: {PE_TEAL}; --pe-red: {PE_RED};
    --pe-gray: {PE_GRAY}; --pe-light: {PE_LIGHT}; --pe-gold: {PE_GOLD};
  }}
  @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
  html, body {{ margin: 0; padding: 0; font-family: {PE_FONT}; color: var(--pe-gray); background: #FAFAFA; }}
  .wrap {{ max-width: 1180px; margin: 0 auto; padding: 36px 28px 60px; background: white; box-shadow: 0 0 14px rgba(0,0,0,0.05); }}
  header {{ border-bottom: 3px solid var(--pe-blue); padding-bottom: 18px; margin-bottom: 28px; }}
  header h1 {{ font-family: {PE_FONT}; color: var(--pe-blue); margin: 6px 0 2px 0; font-size: 30px; font-weight: 500; }}
  h2 {{ color: var(--pe-blue); margin-top: 40px; font-weight: 500; font-size: 22px; }}
  h3 {{ color: var(--pe-blue); margin-top: 26px; font-weight: 500; font-size: 17px; }}
  p, li {{ font-size: 14.5px; line-height: 1.55; }}
  a {{ color: var(--pe-blue); }}
  .lede {{ font-size: 16px; line-height: 1.6; color: #333; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; margin: 22px 0; }}
  .kpi {{ background: linear-gradient(180deg, #FAFCFE, #F3F7FB); border-left: 4px solid var(--pe-blue); padding: 16px 18px; border-radius: 6px; }}
  .kpi-label {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--pe-gray); }}
  .kpi-value {{ font-size: 28px; font-weight: 500; color: var(--pe-blue); margin: 6px 0 2px; }}
  .kpi-sub {{ font-size: 12px; color: var(--pe-gray); opacity: 0.8; }}
  table {{ border-collapse: collapse; margin: 12px 0 20px; width: 100%; font-size: 13px; }}
  table th {{ background: #F0F4F8; color: var(--pe-blue); font-weight: 600; padding: 8px 10px; text-align: left; border-bottom: 2px solid var(--pe-blue); }}
  table td {{ padding: 7px 10px; border-bottom: 1px solid #ECECEC; }}
  table tr:hover td {{ background: #F8FAFC; }}
  .callout {{ background: #FFF8EA; border-left: 4px solid var(--pe-gold); padding: 14px 18px; margin: 18px 0; border-radius: 4px; }}
</style>
"""


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><title>Impact of cancelling the planned fuel duty rise</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
{css}
</head><body>
<div class="wrap">

<header>
  <h1>Impact of cancelling the planned fuel duty rise</h1>
</header>

<p class="lede">Rachel Reeves is expected to announce on Thursday that she is shelving the planned 5p fuel-duty reversal. This briefing reports the cost of extending the cut, the revenue lost since the first freeze in 2011, the duty rate under an RPI counterfactual, the distributional impact, and the cross-check against the <a href="https://www.theguardian.com/politics/2026/may/18/rachel-reeves-fuel-duty-cost-of-living">Guardian</a> and Fleet News figures.</p>

<div class="kpi-grid">
  <div class="kpi"><div class="kpi-label">Cost of cancelling the planned 5p reversal (2027-28)</div><div class="kpi-value">£{scrap_2027:.2f} bn</div><div class="kpi-sub"><a href="https://www.theguardian.com/politics/2026/may/18/rachel-reeves-fuel-duty-cost-of-living">Guardian</a>-style 5p-only framing for the same year: £{guardian_2027:.2f} bn (matches <a href="https://www.theguardian.com/politics/2026/may/18/rachel-reeves-fuel-duty-cost-of-living">Guardian</a> £2.4 bn / yr)</div></div>
  <div class="kpi"><div class="kpi-label">Cumulative cost of freezes 2010-11 → 2026-27</div><div class="kpi-value">£{fleet_cumulative:.0f} bn</div><div class="kpi-sub">RPI counterfactual · matches Fleet News £120bn</div></div>
  <div class="kpi"><div class="kpi-label">Rate today if uprated by RPI since 2011</div><div class="kpi-value">{counterfactual_rate:.1f}p / L</div><div class="kpi-sub">vs actual {actual_rate:.1f}p · {rate_multiplier:.2f}× current</div></div>
  <div class="kpi"><div class="kpi-label">Annual revenue gap by {last_year_fy} (RPI counterfactual vs actual)</div><div class="kpi-value">£{revenue_gap:.0f} bn</div><div class="kpi-sub">If duty had risen with RPI: £{revenue_counterfactual:.0f}bn / yr · Current law: £{revenue_actual:.0f}bn / yr</div></div>
</div>

<h2>The story so far</h2>
<p>Fuel duty is the per-litre tax on petrol and diesel at the pump. The rate has been frozen every year since Budget 2011. In March 2022 Rishi Sunak cut it by a further 5p (from 57.95p to 52.95p) as a temporary measure. The Autumn Budget 2025 set out a phased reversal of that cut — 1p in September 2026, 2p in December 2026, 2p in March 2027 — followed by annual RPI uprating from April 2027 onwards. Reeves is expected to cancel the September 1p step-up and may cancel all of the 5p reversal; the press reports do not address the April-2027 RPI uprating.</p>

<h2>How much does scrapping the 5p increase cost?</h2>
<p>The Autumn Budget 2025 schedule increases the duty by 1p in September 2026, 2p in December 2026, 2p in March 2027, then uprates by RPI each April. Holding the rate at 52.95p instead, the annual revenue forgone is:</p>

{chart1}

{scrap_5p_table}

<h2>What would the rate be if it had risen with RPI since 2011?</h2>
<p>Compounding RPI annually onto the 57.95p rate frozen in Budget 2011 gives the counterfactual path below.</p>

{chart2}

<h2>How much money have the freezes lost so far?</h2>
<p>The chart combines three series:</p>
<ul>
  <li><strong>Yellow line — HMRC out-turn (2010-11 to 2024-25)</strong>: fuel-duty receipts as published in HMRC's UK Tax & NICs receipts statistics on gov.uk.</li>
  <li><strong>Blue line — OBR forecast (2025-26 to {last_year_fy})</strong>: March 2026 OBR fuel-duty receipts at the current-law rate schedule.</li>
  <li><strong>Dashed teal line — RPI counterfactual</strong>: each year's current-law revenue plus the OBR/HMRC litre benchmark for the counterfactual duty-rate gap.</li>
</ul>

{chart3}

<h2>Does this match the <a href="https://www.theguardian.com/politics/2026/may/18/rachel-reeves-fuel-duty-cost-of-living">Guardian</a> and Fleet News?</h2>
<p>The two press reports on 18 May 2026 quoted £2.4 bn / year (<a href="https://www.theguardian.com/politics/2026/may/18/rachel-reeves-fuel-duty-cost-of-living">Guardian</a>) and ~£120 bn cumulative since 2010/11 (Fleet News). Both use the "extend the 5p cut" framing: 52.95p kept versus a return to 57.95p, with no further RPI uprating. In 2027-28, the OBR/HMRC road-fuel benchmark puts that figure at £{guardian_2027:.2f} bn (and £{guardian_2026:.2f} bn in 2026-27), while the cumulative cost of freezes from 2010/11 to 2026/27 comes to £{fleet_cumulative:.1f} bn — both consistent with the press numbers. The earlier "How much does scrapping the 5p increase cost?" section reports a higher 2027-28 figure (£{scrap_2027:.2f} bn) because it compares against {baseline_rate_2027:.2f}p — i.e. 57.95p plus the April-2027 RPI uprating that the Autumn Budget 2025 plan would also have brought in. The £{scrap_minus_guardian:.2f} bn difference is the cost of cancelling that RPI uprating on top of the 5p reversal.</p>

<h2>Who gains from cancelling the planned rise?</h2>
<p>Person-weighted average household saving from keeping duty at 52.95p/L rather than following the full Autumn Budget 2025 plan for 2027-28 ({baseline_rate_2027:.2f}p/L), as a share of household net income. The bottom 5% by equivalised income is excluded from all three cuts (the Resolution Foundation approach, used in <a href="https://resolutionfoundation.substack.com/p/higher-energy-prices-could-leave">their energy-price analysis</a> to remove data-reliability concerns about the very lowest reported incomes). The remaining 95% is then split into quartiles, quintiles and deciles.</p>

<h3>By income quartile</h3>
{chart_quart}
{quartiles_table}

<h3>By income quintile</h3>
{chart_quint}
{quintiles_table}

<h3>By income decile</h3>
{chart_dec}
{deciles_table}

<h2>Headline numbers</h2>
<table>
  <thead><tr><th>Question</th><th>Answer</th></tr></thead>
  <tbody>
    <tr><td>Cost of extending the 5p cut (Guardian framing)</td><td><strong>£{guardian_2026:.2f}bn</strong> in 2026-27 · £{guardian_2027:.2f}bn in 2027-28</td></tr>
    <tr><td>Cost of cancelling the full Autumn Budget 2025 plan</td><td>£{scrap_2027:.2f}bn (2027-28) → £{scrap_2029:.2f}bn ({last_year_fy}) · cumulative <strong>£{cumulative:.1f}bn</strong> through {last_year_fy}</td></tr>
    <tr><td>Cumulative cost of freezes 2010-11 → 2026-27</td><td><strong>£{fleet_cumulative:.0f}bn</strong></td></tr>
    <tr><td>Rate today if uprated by RPI since 2011</td><td><strong>{counterfactual_rate:.1f}p / L</strong> vs actual {actual_rate:.1f}p · {rate_multiplier:.2f}× current</td></tr>
    <tr><td>Annual revenue gap by {last_year_fy} vs counterfactual</td><td><strong>£{revenue_gap:.0f}bn</strong></td></tr>
    <tr><td>Person-weighted average household saving from cancelling the planned rise</td><td>~£{avg_saving:.0f}/yr (2027)</td></tr>
  </tbody>
</table>

<h2>Sources</h2>
<ul>
  <li>Distributional household figures: <code>{citation}</code>.</li>
  <li>Method note: {method_note}</li>
  <li>Headline fiscal totals: HMRC road-fuel clearances and UK Tax & NICs receipts; OBR March 2026 fuel-duty receipts forecast.</li>
  <li>RPI series: OBR Economic and Fiscal Outlook, March 2026.</li>
  <li>No behavioural responses modelled: fuel volumes held fixed across scenarios.</li>
</ul>

</div></body></html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT, type=Path)
    args = parser.parse_args()
    path = build(args.output)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
