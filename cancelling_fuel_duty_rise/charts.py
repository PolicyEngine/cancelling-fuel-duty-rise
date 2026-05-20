"""Plotly chart builders. All return ``plotly.graph_objects.Figure``."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .theme import PE_BLUE, PE_FONT, PE_GOLD, PE_GRAY, PE_RED, PE_TEAL


def annual_cost_chart(scrap_5p: pd.DataFrame, *, from_year: int = 2026) -> go.Figure:
    """Bar chart: annual cost of cancelling the planned 5p reversal."""
    df = scrap_5p[scrap_5p["Year"] >= from_year].copy()
    fy_labels = [f"{y}-{(y + 1) % 100:02d}" for y in df["Year"]]
    fig = px.bar(
        df,
        x=fy_labels,
        y="Cost to Treasury (£bn)",
        text=df["Cost to Treasury (£bn)"].map(lambda v: f"£{v:.2f}bn"),
        title="Annual cost of scrapping the planned 5p reversal",
        labels={"x": "Fiscal year", "Cost to Treasury (£bn)": "£ billion forgone"},
    )
    fig.update_traces(
        marker_color=PE_BLUE,
        textposition="outside",
        textfont=dict(family=PE_FONT, color=PE_BLUE, size=12),
    )
    fig.update_layout(height=460, showlegend=False)
    return fig


def rate_path_chart(rate_path: pd.DataFrame) -> go.Figure:
    """Line chart: actual rate vs RPI counterfactual rate 2011-2029."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=rate_path["year"],
            y=rate_path["actual_rate_p_per_litre"],
            name="Actual rate",
            mode="lines",
            line=dict(color=PE_BLUE, width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=rate_path["year"],
            y=rate_path["rpi_counterfactual_rate_p_per_litre"],
            name="RPI counterfactual",
            mode="lines",
            line=dict(color=PE_TEAL, width=3, dash="dash"),
        )
    )
    from .volumes import FIRST_FREEZE_YEAR, FIVE_PENCE_CUT_YEAR

    fig.add_vline(
        x=FIRST_FREEZE_YEAR,
        line_width=1,
        line_dash="dot",
        line_color=PE_GRAY,
        annotation_text=f"1st freeze (Budget {FIRST_FREEZE_YEAR})",
        annotation_position="top",
        annotation_font=dict(family=PE_FONT, color=PE_GRAY, size=10),
    )
    fig.add_vline(
        x=FIVE_PENCE_CUT_YEAR,
        line_width=1,
        line_dash="dot",
        line_color=PE_GRAY,
        annotation_text=f"5p cut (Mar {FIVE_PENCE_CUT_YEAR})",
        annotation_position="top",
        annotation_font=dict(family=PE_FONT, color=PE_GRAY, size=10),
    )
    fig.update_layout(
        title="Fuel duty: actual rate vs RPI-uprated counterfactual",
        xaxis_title="Year",
        yaxis_title="Pence per litre",
        height=520,
        legend=dict(x=0.02, y=0.98),
    )
    return fig


def obr_style_chart(revenue: pd.DataFrame) -> go.Figure:
    """OBR-style chart with HMRC out-turn, PE-UK projection and RPI
    counterfactual line + gap arrow.

    The split between out-turn and projection is taken from the ``source``
    column of *revenue* (no hard-coded year), and the counterfactual line
    starts from the first year with a non-zero rate gap.
    """
    years_all = revenue["year"].tolist()
    last_outturn_year = revenue.loc[
        revenue["source"] == "HMRC out-turn", "year"
    ].max()
    cf_start_year = revenue.loc[
        revenue["counterfactual_revenue_gbp_bn"]
        > revenue["actual_revenue_gbp_bn"] + 1e-6,
        "year",
    ].min()
    hist = revenue[revenue["year"] <= last_outturn_year]
    fcst = revenue[revenue["year"] >= last_outturn_year]
    cf = revenue[revenue["year"] >= cf_start_year]
    last_y = max(years_all)
    last_row = revenue[revenue["year"] == last_y].iloc[0]
    gap_value = (
        last_row["counterfactual_revenue_gbp_bn"]
        - last_row["actual_revenue_gbp_bn"]
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=hist["year"],
            y=hist["actual_revenue_gbp_bn"],
            name="Fuel-duty revenue — HMRC out-turn",
            mode="lines",
            line=dict(color=PE_GOLD, width=3.2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=fcst["year"],
            y=fcst["actual_revenue_gbp_bn"],
            name="Fuel-duty revenue — PolicyEngine UK projection",
            mode="lines",
            line=dict(color=PE_BLUE, width=3.2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=cf["year"],
            y=cf["counterfactual_revenue_gbp_bn"],
            name="RPI counterfactual (uprated annually since 2011)",
            mode="lines",
            line=dict(color=PE_TEAL, width=3.6, dash="dash"),
        )
    )
    fig.add_annotation(
        x=last_y + 0.35,
        y=last_row["counterfactual_revenue_gbp_bn"],
        ax=last_y + 0.35,
        ay=last_row["actual_revenue_gbp_bn"],
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=3,
        arrowsize=1.2,
        arrowwidth=2.5,
        arrowcolor=PE_RED,
    )
    fig.add_annotation(
        x=last_y + 0.75,
        y=(
            last_row["counterfactual_revenue_gbp_bn"]
            + last_row["actual_revenue_gbp_bn"]
        )
        / 2,
        text=f"<b>£{gap_value:.0f}bn<br>gap</b>",
        showarrow=False,
        font=dict(family=PE_FONT, color=PE_RED, size=14),
        xanchor="left",
    )
    from .volumes import FIRST_FREEZE_YEAR, FIVE_PENCE_CUT_YEAR

    fig.add_vline(
        x=FIRST_FREEZE_YEAR,
        line_width=1,
        line_dash="dot",
        line_color=PE_GRAY,
        annotation_text=f"1st freeze (Budget {FIRST_FREEZE_YEAR})",
        annotation_position="bottom",
        annotation_font=dict(family=PE_FONT, color=PE_GRAY, size=10),
    )
    fig.add_vline(
        x=FIVE_PENCE_CUT_YEAR,
        line_width=1,
        line_dash="dot",
        line_color=PE_GRAY,
        annotation_text=f"5p cut (Mar {FIVE_PENCE_CUT_YEAR})",
        annotation_position="bottom",
        annotation_font=dict(family=PE_FONT, color=PE_GRAY, size=10),
    )
    tickvals = [y for y in years_all if y % 2 == 0]
    fig.update_layout(
        title=f"Fuel duties: actual vs RPI-uprated counterfactual (2010-11 → {last_y}-{(last_y + 1) % 100:02d})",
        xaxis=dict(
            tickmode="array",
            tickvals=tickvals,
            ticktext=[f"{y}-{(y + 1) % 100:02d}" for y in tickvals],
            tickangle=-45,
            range=[2009.5, last_y + 2.3],
        ),
        yaxis=dict(
            title="£ billion",
            range=[0, revenue["counterfactual_revenue_gbp_bn"].max() * 1.10],
        ),
        height=600,
        legend=dict(x=0.02, y=0.98),
    )
    return fig


def distributional_chart(
    df: pd.DataFrame, *, group_label: str, title: str
) -> go.Figure:
    """Bar chart: saving as % of net income by income group."""
    fig = px.bar(
        df,
        x="group",
        y="saving_pct_of_net_income",
        title=title,
        labels={
            "group": group_label,
            "saving_pct_of_net_income": "% of household net income",
        },
        text=df["saving_pct_of_net_income"].map(lambda v: f"{v:.2f}%"),
    )
    fig.update_traces(
        marker_color=PE_BLUE,
        textposition="outside",
        textfont=dict(family=PE_FONT, color=PE_BLUE, size=11),
    )
    fig.update_layout(
        height=440, yaxis=dict(ticksuffix="%"), showlegend=False
    )
    return fig
