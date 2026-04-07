"""Unit tests for htcie chart figure builders."""

from __future__ import annotations

import plotly.graph_objects as go

from htcie.gui.components.charts import (
    build_ranking_lollipop,
    build_uncertainty_lollipop,
)


def test_ranking_lollipop_returns_figure() -> None:
    ranking = [
        {"key": "internal.gnielinski", "score": 0.85},
        {"key": "internal.dittus_boelter", "score": 0.62},
    ]
    fig = build_ranking_lollipop(ranking)
    assert isinstance(fig, go.Figure)


def test_ranking_lollipop_first_dot_is_accent_colored() -> None:
    """Best-ranked item's dot should use _COLOR_BEST (sky blue)."""
    ranking = [
        {"key": "internal.gnielinski", "score": 0.85},
        {"key": "internal.dittus_boelter", "score": 0.62},
    ]
    fig = build_ranking_lollipop(ranking)
    # N stems + 1 dot trace
    assert len(fig.data) == len(ranking) + 1
    dot_trace = fig.data[-1]
    assert dot_trace.marker.color[0] == "#0ea5e9"


def test_ranking_lollipop_x_range() -> None:
    ranking = [{"key": "internal.gnielinski", "score": 0.75}]
    fig = build_ranking_lollipop(ranking)
    assert list(fig.layout.xaxis.range) == [0, 1]


def test_ranking_lollipop_empty_returns_empty_figure() -> None:
    fig = build_ranking_lollipop([])
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0


def test_uncertainty_lollipop_returns_figure() -> None:
    evaluations = [
        {
            "key": "internal.gnielinski",
            "h": 3678.0,
            "h_low": 3310.2,
            "h_high": 4045.8,
            "uncertainty_pct": 10.0,
            "uncertainty_note": "",
        }
    ]
    ranking = [{"key": "internal.gnielinski", "score": 0.85}]
    fig = build_uncertainty_lollipop(evaluations, ranking)
    assert isinstance(fig, go.Figure)


def test_uncertainty_lollipop_ordered_by_ranking() -> None:
    """Evaluations must appear in ranking order (best first)."""
    evaluations = [
        {
            "key": "internal.dittus_boelter",
            "h": 3000.0,
            "h_low": None,
            "h_high": None,
            "uncertainty_pct": None,
            "uncertainty_note": "",
        },
        {
            "key": "internal.gnielinski",
            "h": 3678.0,
            "h_low": 3310.2,
            "h_high": 4045.8,
            "uncertainty_pct": 10.0,
            "uncertainty_note": "",
        },
    ]
    ranking = [
        {"key": "internal.gnielinski", "score": 0.85},
        {"key": "internal.dittus_boelter", "score": 0.62},
    ]
    fig = build_uncertainty_lollipop(evaluations, ranking)
    # Dot trace is the last trace; its y values should be in ranking order
    dot_trace = fig.data[-1]
    assert dot_trace.y[0] == "gnielinski"
    assert dot_trace.y[1] == "dittus_boelter"


def test_uncertainty_lollipop_empty_inputs() -> None:
    fig = build_uncertainty_lollipop([], [])
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0


def test_uncertainty_lollipop_no_band_suppresses_error_x() -> None:
    """When no evaluation has h_low/h_high, error_x should be None."""
    evaluations = [
        {
            "key": "internal.gnielinski",
            "h": 3678.0,
            "h_low": None,
            "h_high": None,
            "uncertainty_pct": None,
            "uncertainty_note": "",
        },
    ]
    ranking = [{"key": "internal.gnielinski", "score": 0.85}]
    fig = build_uncertainty_lollipop(evaluations, ranking)
    dot_trace = fig.data[-1]
    assert dot_trace.error_x is None or not dot_trace.error_x.visible
