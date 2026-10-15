"""Pareto Efficiency Frontier (Value-for-Money) analysis module for SmartPick AI.

Implements Phase P5a Requirement 2:
Computes the price-vs-spec efficiency frontier (Pareto optimal set) for eligible smartphones.
A device lies on the Pareto frontier if no other device offers equal or superior hardware
specifications at a lower or equal price.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.preprocessing import DEFAULT_FEATURE_COLUMNS, FeaturePreprocessor


def compute_pareto_frontier(
    candidates_df: pd.DataFrame,
    preprocessor: FeaturePreprocessor,
) -> pd.DataFrame:
    """Identify devices on the price-vs-hardware specification Pareto efficiency frontier.

    Methodology:
    1. Composite Hardware Capability Score H(d) in [0, 100]:
       Computed as the mean of scaled specifications (processor, camera, battery, display,
       storage, and RAM) using fitted outlier-resilient bounds.
    2. Pareto Dominance:
       Device A dominates Device B if:
       - Price(A) <= Price(B) AND Hardware(A) >= Hardware(B), and
       - At least one inequality is strict.
    3. Frontier Set:
       Devices that are not dominated by any other device in the candidate set.

    Args:
        candidates_df: Eligible catalog candidates satisfying budget bounds.
        preprocessor: Fitted FeaturePreprocessor instance.

    Returns:
        DataFrame with added columns: 'hardware_score', 'is_pareto_optimal', 'efficiency_status'.
    """
    if candidates_df.empty:
        return candidates_df.copy()

    df = candidates_df.copy()

    # Scale numeric specs
    scaled_df = preprocessor.transform(df)
    active_cols = [c for c in DEFAULT_FEATURE_COLUMNS if c in scaled_df.columns]

    # Compute composite hardware score (0 to 100)
    hw_score = scaled_df[active_cols].mean(axis=1, skipna=True) * 100.0
    df["hardware_score"] = hw_score.round(1)

    prices = df["price_inr"].to_numpy(dtype=float)
    scores = df["hardware_score"].to_numpy(dtype=float)
    n = len(df)

    is_frontier = np.ones(n, dtype=bool)

    # Pairwise Pareto dominance check
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            # Device j dominates device i if j is cheaper/equal AND j has higher/equal score, with strict diff
            if (prices[j] <= prices[i] and scores[j] >= scores[i]) and (
                prices[j] < prices[i] or scores[j] > scores[i]
            ):
                is_frontier[i] = False
                break

    df["is_pareto_optimal"] = is_frontier
    df["efficiency_status"] = np.where(
        is_frontier, "💎 Pareto Efficient (Top Value)", "Standard Candidate"
    )

    return df


def render_pareto_frontier_chart(
    frontier_df: pd.DataFrame,
    recommended_names: list[str] | None = None,
) -> go.Figure:
    """Create interactive Plotly scatter plot with connected Pareto efficiency frontier line.

    Args:
        frontier_df: DataFrame with 'price_inr', 'hardware_score', 'is_pareto_optimal'.
        recommended_names: Optional list of phones recommended in current user session.

    Returns:
        Plotly Figure object.
    """
    rec_names = recommended_names or []
    df = frontier_df.copy()

    non_frontier = df[~df["is_pareto_optimal"]]
    frontier = df[df["is_pareto_optimal"]].sort_values("price_inr")

    fig = go.Figure()

    # 1. Background Non-frontier devices
    fig.add_trace(
        go.Scatter(
            x=non_frontier["price_inr"],
            y=non_frontier["hardware_score"],
            mode="markers",
            name="Eligible Devices",
            marker={"color": "#64748B", "size": 8, "opacity": 0.55},
            text=non_frontier["phone_name"],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Price: ₹%{x:,.0f}<br>"
                "Hardware Score: %{y:.1f}/100<br>"
                "Status: Dominated (Sub-optimal spec/price ratio)<extra></extra>"
            ),
        )
    )

    # 2. Frontier Connecting Line (Efficiency Boundary)
    if len(frontier) >= 2:
        fig.add_trace(
            go.Scatter(
                x=frontier["price_inr"],
                y=frontier["hardware_score"],
                mode="lines",
                name="Pareto Frontier Boundary",
                line={"color": "#38BDF8", "width": 2, "dash": "dot"},
                hoverinfo="skip",
            )
        )

    # 3. Frontier Optimal Devices
    fig.add_trace(
        go.Scatter(
            x=frontier["price_inr"],
            y=frontier["hardware_score"],
            mode="markers+text",
            name="💎 Pareto Frontier (Top Value)",
            marker={
                "color": "#10B981",
                "size": 13,
                "symbol": "diamond",
                "line": {"color": "#FFFFFF", "width": 1.5},
            },
            text=frontier["phone_name"],
            textposition="top center",
            textfont={"color": "#F8FAFC", "size": 10},
            hovertemplate=(
                "<b>💎 %{text}</b><br>"
                "Price: ₹%{x:,.0f}<br>"
                "Hardware Score: %{y:.1f}/100<br>"
                "Status: <b>Pareto Efficient</b> (Unmatched spec-to-rupee ratio)<extra></extra>"
            ),
        )
    )

    # 4. Highlight User's Recommended Shortlist
    rec_df = df[df["phone_name"].isin(rec_names)]
    if not rec_df.empty:
        fig.add_trace(
            go.Scatter(
                x=rec_df["price_inr"],
                y=rec_df["hardware_score"],
                mode="markers",
                name="⭐ Current Recommendations",
                marker={
                    "color": "#FBBF24",
                    "size": 16,
                    "symbol": "star",
                    "line": {"color": "#1E293B", "width": 2},
                },
                text=rec_df["phone_name"],
                hovertemplate=(
                    "<b>⭐ %{text}</b><br>"
                    "Price: ₹%{x:,.0f}<br>"
                    "Hardware Score: %{y:.1f}/100<br>"
                    "Status: Top Recommendation<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title="Price-vs-Hardware Pareto Efficiency Frontier (Microeconomic Value Analysis)",
        xaxis_title="Price (₹ INR)",
        yaxis_title="Composite Hardware Capability Index (0-100)",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 23, 42, 0.6)",
        font={"color": "#F8FAFC", "family": "Inter, sans-serif"},
        xaxis={
            "gridcolor": "rgba(255, 255, 255, 0.08)",
            "zerolinecolor": "rgba(255, 255, 255, 0.12)",
        },
        yaxis={
            "gridcolor": "rgba(255, 255, 255, 0.08)",
            "zerolinecolor": "rgba(255, 255, 255, 0.12)",
            "range": [0, 105],
        },
    )
    return fig
