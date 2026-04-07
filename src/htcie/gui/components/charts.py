"""Plotly chart components for htcie GUI."""

from __future__ import annotations

import plotly.graph_objects as go
from nicegui import ui

# Shared colour constants
_COLOR_BEST = "#0ea5e9"  # sky blue — top-ranked method
_COLOR_REST = "#94a3b8"  # slate grey — all others
_COLOR_STEM_OPACITY = 0.5


def _lollipop_colors(n: int) -> list[str]:
    """Return per-item colors: accent for first, muted for rest."""
    return [_COLOR_BEST if i == 0 else _COLOR_REST for i in range(n)]


def build_ranking_lollipop(ranking: list[dict], show_title: bool = True) -> go.Figure:
    """Build a horizontal lollipop figure comparing ranking scores.

    Returns an empty Figure when ranking is empty.

    Args:
        ranking: List of dicts with 'key' and 'score' fields.
    """
    if not ranking:
        return go.Figure()

    labels = [r["key"].split(".")[-1] for r in ranking]
    scores = [r["score"] for r in ranking]
    colors = _lollipop_colors(len(labels))

    fig = go.Figure()

    # Stems: one trace per item so each can carry its own accent color
    for label, score, color in zip(labels, scores, colors):
        fig.add_trace(
            go.Scatter(
                x=[0, score],
                y=[label, label],
                mode="lines",
                line={"color": color, "width": 2},
                opacity=_COLOR_STEM_OPACITY,
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Dots with score labels to the right
    fig.add_trace(
        go.Scatter(
            x=scores,
            y=labels,
            mode="markers+text",
            marker={
                "color": colors,
                "size": 12,
                "line": {"color": "white", "width": 1.5},
            },
            text=[f"{s:.3f}" for s in scores],
            textposition="middle right",
            textfont={"size": 11},
            hovertemplate="%{y}<br>Score: %{text}<extra></extra>",
            showlegend=False,
        )
    )

    x_max = max(1.0, max(scores) + 0.12)

    fig.update_layout(
        title="<b>Correlation Ranking Score</b>" if show_title else None,
        xaxis={
            "title": "Score",
            "range": [0, x_max],
            "showgrid": True,
            "gridcolor": "#e2e8f0",
            "zeroline": False,
        },
        yaxis={"showgrid": False, "autorange": "reversed"},
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin={"l": 20, "r": 20, "t": 10 if not show_title else 40, "b": 40},
        height=max(200, 60 + 40 * len(labels)),
        autosize=True,
    )
    return fig


def render_ranking_chart(ranking: list[dict]) -> None:
    """Render ranking lollipop chart in the current NiceGUI context."""
    if not ranking:
        return
    with ui.element("div").style(
        "border: 1px solid #cbd5e1; border-radius: 4px; width: 100%;"
    ):
        ui.plotly(build_ranking_lollipop(ranking, show_title=False)).classes("w-full")


def build_uncertainty_lollipop(
    evaluations: list[dict], ranking: list[dict], show_title: bool = True
) -> go.Figure:
    """Build a horizontal lollipop figure for h with uncertainty bands.

    Evaluations are ordered best-first using the ranking list.
    Returns an empty Figure when inputs are empty.

    Args:
        evaluations: List of evaluation dicts with 'key', 'h', 'h_low',
            'h_high', 'uncertainty_pct', 'uncertainty_note' fields.
        ranking: List of ranking dicts with 'key' field (defines order).
    """
    if not evaluations or not ranking:
        return go.Figure()

    ranking_order = {r["key"]: i for i, r in enumerate(ranking)}
    sorted_evals = sorted(
        evaluations,
        key=lambda e: ranking_order.get(e["key"], len(ranking)),
    )

    labels = [e["key"].split(".")[-1] for e in sorted_evals]
    h_values = [e["h"] for e in sorted_evals]
    colors = _lollipop_colors(len(labels))

    error_plus: list[float | None] = []
    error_minus: list[float | None] = []
    for e in sorted_evals:
        h = e["h"]
        h_low = e.get("h_low")
        h_high = e.get("h_high")
        if h_low is not None and h_high is not None and h is not None:
            error_plus.append(h_high - h)
            error_minus.append(h - h_low)
        else:
            error_plus.append(None)
            error_minus.append(None)

    hover_texts = []
    for e in sorted_evals:
        h = e["h"]
        pct = e.get("uncertainty_pct")
        h_low = e.get("h_low")
        h_high = e.get("h_high")
        note = e.get("uncertainty_note", "")
        if h_low is not None and h_high is not None and pct is not None:
            hover_texts.append(
                f"{e['key']}<br>h = {h:.1f} W/m²·K"
                f"<br>±{pct:.0f}%"
                f"<br>[{h_low:.1f}, {h_high:.1f}]"
            )
        else:
            hover_texts.append(
                f"{e['key']}<br>h = {h:.1f} W/m²·K<br>{note or 'No uncertainty band'}"
            )

    fig = go.Figure()

    # Stems
    for i, (label, h, color) in enumerate(zip(labels, h_values, colors)):
        fig.add_trace(
            go.Scatter(
                x=[0, h],
                y=[label, label],
                mode="lines",
                line={"color": color, "width": 2},
                opacity=_COLOR_STEM_OPACITY,
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Dots with optional horizontal error bars and h value labels above
    has_any_band = any(v is not None for v in error_plus)
    fig.add_trace(
        go.Scatter(
            x=h_values,
            y=labels,
            mode="markers+text",
            marker={
                "color": colors,
                "size": 12,
                "line": {"color": "white", "width": 1.5},
            },
            error_x=dict(
                type="data",
                array=error_plus,
                arrayminus=error_minus,
                visible=True,
                color=_COLOR_REST,
                thickness=2,
                width=6,
            )
            if has_any_band
            else None,
            text=[f"{h:.1f}" for h in h_values],
            textposition="top center",
            textfont={"size": 11},
            hovertext=hover_texts,
            hovertemplate="%{hovertext}<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        title="<b>Heat Transfer Coefficient with Uncertainty</b>"
        if show_title
        else None,
        xaxis={
            "title": "h [W/m²·K]",
            "showgrid": True,
            "gridcolor": "#e2e8f0",
            "zeroline": False,
        },
        yaxis={"showgrid": False, "range": [len(labels) - 0.5, -0.7]},
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin={"l": 20, "r": 20, "t": 10 if not show_title else 40, "b": 40},
        height=max(200, 60 + 40 * len(labels)),
        autosize=True,
    )
    return fig


def render_uncertainty_chart(evaluations: list[dict], ranking: list[dict]) -> None:
    """Render h-with-uncertainty lollipop chart in the current NiceGUI context."""
    if not evaluations or not ranking:
        return
    with ui.element("div").style(
        "border: 1px solid #cbd5e1; border-radius: 4px; width: 100%;"
    ):
        ui.plotly(
            build_uncertainty_lollipop(evaluations, ranking, show_title=False)
        ).classes("w-full")
