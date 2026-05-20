"""PolicyEngine brand palette and Plotly template."""

import plotly.graph_objects as go
import plotly.io as pio

PE_BLUE = "#2C6496"
PE_TEAL = "#39C6C0"
PE_RED = "#b50d0d"
PE_GRAY = "#616161"
PE_GREEN = "#29D40F"
PE_GOLD = "#F2BC1B"
PE_LIGHT = "#F2F2F2"
PE_FONT = 'Roboto, "Helvetica Neue", Arial, sans-serif'


def register_template() -> None:
    """Register and activate the PolicyEngine Plotly template."""
    pio.templates["policyengine"] = go.layout.Template(
        layout=go.Layout(
            font=dict(family=PE_FONT, size=13, color=PE_GRAY),
            title=dict(font=dict(family=PE_FONT, size=17, color=PE_BLUE)),
            colorway=[PE_BLUE, PE_TEAL, PE_RED, PE_GOLD, PE_GREEN, PE_GRAY],
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis=dict(
                showgrid=True,
                gridcolor=PE_LIGHT,
                zeroline=False,
                linecolor=PE_GRAY,
                ticks="outside",
                tickcolor=PE_GRAY,
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=PE_LIGHT,
                zeroline=False,
                linecolor=PE_GRAY,
                ticks="outside",
                tickcolor=PE_GRAY,
            ),
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                font=dict(family=PE_FONT, size=12, color=PE_GRAY),
            ),
            margin=dict(l=70, r=40, t=70, b=70),
        )
    )
    pio.templates.default = "policyengine"
