"""Plotly data visualization components for SmartPick AI.

Implements:
- Contribution stacked bar chart (preference score composition per device)
- Price distribution histogram with active budget overlay
- Price vs. Battery scatter plot with recommended devices highlighted
- Multi-device radar chart for side-by-side spec comparison
- User preference weight profile allocation
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.recommender import RecommendationResult, UserPreferences

# Cohesive WCAG AA dark-theme Plotly layout
DARK_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(15, 23, 42, 0.6)",
        "font": {"color": "#F8FAFC", "family": "Inter, sans-serif"},
        "margin": {"t": 40, "b": 40, "l": 40, "r": 20},
        "xaxis": {
            "gridcolor": "rgba(255, 255, 255, 0.08)",
            "zerolinecolor": "rgba(255, 255, 255, 0.12)",
        },
        "yaxis": {
            "gridcolor": "rgba(255, 255, 255, 0.08)",
            "zerolinecolor": "rgba(255, 255, 255, 0.12)",
        },
    }
}

DIMENSION_COLORS: dict[str, str] = {
    "performance": "#2563EB",  # Sapphire Blue
    "camera": "#8B5CF6",  # Purple
    "battery": "#10B981",  # Emerald Green
    "display": "#06B6D4",  # Cyan
    "storage": "#F59E0B",  # Amber
    "value": "#F43F5E",  # Rose
}


def render_contribution_bar(results: list[RecommendationResult]) -> go.Figure:
    """Create stacked bar chart showing how each preference dimension built the score."""
    records = []
    for r in results:
        row: dict[str, str | float] = {"phone_name": r.phone_name}
        for dim, pts in r.feature_contributions.items():
            row[dim.title()] = pts
        records.append(row)

    df = pd.DataFrame(records)
    dimensions = [c for c in df.columns if c != "phone_name"]

    fig = go.Figure()
    for dim in dimensions:
        dim_key = dim.lower()
        color = DIMENSION_COLORS.get(dim_key, "#3B82F6")
        fig.add_trace(
            go.Bar(
                name=dim,
                y=df["phone_name"],
                x=df[dim],
                orientation="h",
                marker={"color": color},
                hovertemplate=f"<b>%{{y}}</b><br>{dim}: %{{x:.1f}} pts<extra></extra>",
            )
        )

    fig.update_layout(
        barmode="stack",
        title="Score Composition by Preference Dimension (Points out of 100)",
        xaxis_title="Match Score Points",
        yaxis_title="",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        **DARK_TEMPLATE["layout"],
    )
    fig.update_yaxes(autorange="reversed")
    return fig


def render_price_distribution(
    catalog_df: pd.DataFrame, min_budget: float, max_budget: float
) -> go.Figure:
    """Create histogram of catalog prices with active budget window highlighted."""
    valid_prices = catalog_df["price_inr"].dropna()
    valid_prices = valid_prices[valid_prices > 0]

    fig = px.histogram(
        valid_prices,
        x="price_inr",
        nbins=25,
        title="Catalog Price Distribution & Selected Budget Window",
        labels={"price_inr": "Price (₹ INR)"},
        color_discrete_sequence=["#334155"],
    )

    # Shaded budget region
    fig.add_vrect(
        x0=min_budget,
        x1=max_budget,
        fillcolor="rgba(37, 99, 235, 0.25)",
        layer="below",
        line_width=2,
        line_color="#3B82F6",
        annotation_text="Selected Budget",
        annotation_position="top left",
        annotation_font_color="#60A5FA",
    )

    fig.update_layout(
        yaxis_title="Device Count",
        **DARK_TEMPLATE["layout"],
    )
    return fig


def render_price_vs_battery_scatter(
    catalog_df: pd.DataFrame, recommended_names: list[str]
) -> go.Figure:
    """Create scatter plot of Price vs. Battery with recommended devices highlighted."""
    df = catalog_df.dropna(subset=["price_inr", "battery_mah"]).copy()
    df = df[df["price_inr"] > 0]
    df["is_recommended"] = df["phone_name"].isin(recommended_names)

    catalog_phones = df[~df["is_recommended"]]
    rec_phones = df[df["is_recommended"]]

    fig = go.Figure()

    # Catalog background phones
    fig.add_trace(
        go.Scatter(
            x=catalog_phones["price_inr"],
            y=catalog_phones["battery_mah"],
            mode="markers",
            name="Other Catalog Phones",
            marker={"color": "#64748B", "size": 7, "opacity": 0.6},
            text=catalog_phones["phone_name"],
            hovertemplate="<b>%{text}</b><br>Price: ₹%{x:,.0f}<br>Battery: %{y:,.0f} mAh<extra></extra>",
        )
    )

    # Highlighted recommended phones
    if not rec_phones.empty:
        fig.add_trace(
            go.Scatter(
                x=rec_phones["price_inr"],
                y=rec_phones["battery_mah"],
                mode="markers+text",
                name="Top Recommendations",
                marker={
                    "color": "#FBBF24",
                    "size": 14,
                    "symbol": "diamond",
                    "line": {"color": "#FFFFFF", "width": 2},
                },
                text=rec_phones["phone_name"],
                textposition="top center",
                textfont={"color": "#F8FAFC", "size": 11},
                hovertemplate="<b>⭐ %{text}</b><br>Price: ₹%{x:,.0f}<br>Battery: %{y:,.0f} mAh<extra></extra>",
            )
        )

    fig.update_layout(
        title="Price vs. Battery Capacity (Highlighting Shortlisted Phones)",
        xaxis_title="Price (₹ INR)",
        yaxis_title="Battery Capacity (mAh)",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        **DARK_TEMPLATE["layout"],
    )
    return fig


def render_radar_comparison(selected_results: list[RecommendationResult]) -> go.Figure:
    """Create radar chart comparing normalized specs of 2-4 shortlisted phones."""
    categories = ["Performance", "Camera", "Battery", "Display", "Storage"]
    category_keys = [
        "processor_score",
        "camera_mp",
        "battery_mah",
        "display_hz",
        "storage_gb",
    ]

    palette = ["#3B82F6", "#10B981", "#F59E0B", "#EC4899"]
    fig = go.Figure()

    for idx, r in enumerate(selected_results):
        values = []
        for key in category_keys:
            val = r.scaled_specs.get(
                "performance"
                if key == "processor_score"
                else (
                    "camera"
                    if key == "camera_mp"
                    else (
                        "battery"
                        if key == "battery_mah"
                        else ("display" if key == "display_hz" else "storage")
                    )
                ),
                0.0,
            )
            values.append(val * 100.0)

        # Close the polygon loop
        values.append(values[0])
        color = palette[idx % len(palette)]

        fig.add_trace(
            go.Scatterpolar(
                r=values,
                theta=categories + [categories[0]],
                fill="toself",
                name=f"{r.phone_name} (₹{int(r.price_inr):,})",
                line={"color": color, "width": 2},
                fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.2)",
            )
        )

    fig.update_layout(
        title="Multi-Device Specification Profile Comparison",
        polar={
            "radialaxis": {
                "visible": True,
                "range": [0, 100],
                "gridcolor": "rgba(255, 255, 255, 0.1)",
            },
            "angularaxis": {"gridcolor": "rgba(255, 255, 255, 0.1)"},
            "bgcolor": "rgba(15, 23, 42, 0.6)",
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.25,
            "xanchor": "center",
            "x": 0.5,
        },
        **DARK_TEMPLATE["layout"],
    )
    return fig


def render_weight_profile(prefs: UserPreferences) -> go.Figure:
    """Create donut chart showing active preference weight distribution."""
    labels = [
        "Performance",
        "Camera",
        "Battery",
        "Display",
        "Storage",
        "Value for Money",
    ]
    values = [
        prefs.weight_performance,
        prefs.weight_camera,
        prefs.weight_battery,
        prefs.weight_display,
        prefs.weight_storage,
        prefs.weight_value,
    ]

    colors = [DIMENSION_COLORS[k.lower().replace(" for money", "")] for k in labels]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker={"colors": colors},
                textinfo="percent+label",
                insidetextorientation="radial",
                hovertemplate="<b>%{label}</b><br>Weight: %{value:.2f} (%{percent})<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title="Your Configured Priority Profile",
        showlegend=False,
        **DARK_TEMPLATE["layout"],
    )
    return fig
