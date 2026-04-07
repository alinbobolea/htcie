"""Tests for htcie HTML report renderer."""

from __future__ import annotations

from pathlib import Path

from htcie.core.explain import Explanation
from htcie.core.state import (
    BoundaryConditions,
    EngineeringState,
    FlowState,
    FluidProperties,
    Geometry,
)
from htcie.reports.renderer import render_html, save_html
from htcie.reports.schema import HtcieReport


def test_render_html_returns_doctype(sample_report: HtcieReport) -> None:
    html = render_html(sample_report)
    assert isinstance(html, str)
    assert html.strip().startswith("<!DOCTYPE html>")


def test_render_html_contains_method_key(sample_report: HtcieReport) -> None:
    html = render_html(sample_report)
    assert "internal.gnielinski" in html


def test_render_html_contains_reynolds(sample_report: HtcieReport) -> None:
    html = render_html(sample_report)
    re_val = f"{sample_report.derived['reynolds']:.0f}"
    assert re_val in html


def test_render_html_confidence_badge(sample_report: HtcieReport) -> None:
    html = render_html(sample_report)
    assert "badge-high" in html


def test_save_html_writes_file(sample_report: HtcieReport, tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    save_html(sample_report, out)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert len(content) > 500


def test_render_html_all_excluded() -> None:
    """Report with no applicable methods renders without error."""
    state = EngineeringState(
        fluid=FluidProperties(
            density=1000.0,
            viscosity=0.001,
            thermal_conductivity=0.6,
            heat_capacity=4180.0,
        ),
        geometry=Geometry(
            geometry_type="circular_tube",
            characteristic_length=0.025,
            hydraulic_diameter=0.025,
        ),
        boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
        flow=FlowState(velocity=0.4),
    )
    explanation = Explanation(
        best_method="",
        best_score=0.0,
        score_breakdown={},
        why_applicable=[],
        why_others_excluded=[("internal.gnielinski", "Re out of range")],
        key_assumptions=[],
        confidence_class="low",
        extrapolation_warnings=[],
        recommendation_note="No applicable methods.",
    )
    report = HtcieReport(
        input_state=state,
        derived={
            "reynolds": state.reynolds,
            "prandtl": state.prandtl,
            "graetz": None,
            "entry_length_ratio": None,
            "pitch_ratio_transverse": None,
            "pitch_ratio_longitudinal": None,
        },
        applicable=[],
        excluded=[{"key": "internal.gnielinski", "reason": "Re out of range"}],
        evaluations=[],
        ranking=[],
        spread={"count": 0, "mean": None, "stdev": None, "relative_spread": None},
        confidence="low",
        explanation=explanation,
        scoring_weights_version="v1",
    )
    html = render_html(report)
    assert "<!DOCTYPE html>" in html
    assert "No applicable correlations" in html


def test_render_html_with_charts_embeds_html(sample_report: HtcieReport) -> None:
    """Charts dict is passed through to the template unescaped."""
    charts = {
        "ranking": "<div id='rank-chart'>RANK</div>",
        "uncertainty": "<div id='unc-chart'>UNC</div>",
    }
    html = render_html(sample_report, charts=charts)
    assert "<div id='rank-chart'>RANK</div>" in html
    assert "<div id='unc-chart'>UNC</div>" in html


def test_render_html_without_charts_omits_section(sample_report: HtcieReport) -> None:
    """Default render_html call produces no chart markup."""
    html = render_html(sample_report)
    assert "rank-chart" not in html
    assert "unc-chart" not in html


def test_render_html_no_gz_no_warnings(sample_report: HtcieReport) -> None:
    """Report with Gz=None and no extrapolation warnings renders without error."""
    assert sample_report.derived["graetz"] is None
    assert sample_report.explanation.extrapolation_warnings == []
    html = render_html(sample_report)
    assert "<!DOCTYPE html>" in html
