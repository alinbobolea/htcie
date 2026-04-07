"""Tests for uncertainty and confidence classification."""

from __future__ import annotations

import pytest

from htcie.core.registry import CorrelationMetadata
from htcie.core.results import EvaluationResult
from htcie.core.state import (
    BoundaryConditions,
    EngineeringState,
    FlowState,
    FluidProperties,
    Geometry,
)
from htcie.core.uncertainty import (
    UncertaintyEngine,
    confidence_class,
    extrapolation_status,
    summarize_spread,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_state(re: float = 10000.0, pr: float = 0.7) -> EngineeringState:
    """Build a minimal EngineeringState yielding approximately the given Re."""
    rho, mu = 1000.0, 0.001
    L = 0.025
    v = re * mu / (rho * L)
    return EngineeringState(
        fluid=FluidProperties(
            density=rho,
            viscosity=mu,
            thermal_conductivity=0.6,
            heat_capacity=4180.0,
        ),
        geometry=Geometry(
            geometry_type="circular_tube",
            characteristic_length=L,
            hydraulic_diameter=L,
        ),
        boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
        flow=FlowState(velocity=v),
    )


def make_meta(
    re_min: float | None = 3000,
    re_max: float | None = 5e6,
    pr_min: float | None = 0.5,
) -> CorrelationMetadata:
    """Build a minimal CorrelationMetadata with given validity bounds."""
    validity: dict = {}
    if re_min is not None:
        validity["re_min"] = re_min
    if re_max is not None:
        validity["re_max"] = re_max
    if pr_min is not None:
        validity["pr_min"] = pr_min
    return CorrelationMetadata(
        key="internal.test",
        family="convection_internal",
        title="Test",
        output="Nu",
        validity=validity,
        source={"year": 1976},
    )


# ---------------------------------------------------------------------------
# summarize_spread tests
# ---------------------------------------------------------------------------


def test_summarize_spread_empty() -> None:
    result = summarize_spread([])
    assert result["count"] == 0
    assert result["mean"] is None


def test_summarize_spread_single() -> None:
    r = EvaluationResult(key="k", output_name="Nu", value=50.0, metadata={})
    result = summarize_spread([r])
    assert result["mean"] == 50.0
    assert result["stdev"] == 0.0


def test_summarize_spread_multiple() -> None:
    results = [
        EvaluationResult(key="a", output_name="Nu", value=100.0, metadata={}),
        EvaluationResult(key="b", output_name="Nu", value=110.0, metadata={}),
    ]
    summary = summarize_spread(results)
    assert summary["count"] == 2
    assert summary["mean"] == pytest.approx(105.0)
    assert summary["relative_spread"] is not None


# ---------------------------------------------------------------------------
# confidence_class tests
# ---------------------------------------------------------------------------


def test_confidence_high() -> None:
    spread = {"relative_spread": 0.03}
    assert confidence_class(spread) == "high"


def test_confidence_medium() -> None:
    spread = {"relative_spread": 0.10}
    assert confidence_class(spread) == "medium"


def test_confidence_low() -> None:
    spread = {"relative_spread": 0.20}
    assert confidence_class(spread) == "low"


def test_confidence_none_spread_is_low() -> None:
    spread = {"relative_spread": None}
    assert confidence_class(spread) == "low"


def test_confidence_high_blocked_by_extrapolation() -> None:
    spread = {"relative_spread": 0.03}
    # Significant extrapolation should lower confidence
    result = confidence_class(
        spread, extrapolation_warnings=["Re exceeds re_max by 50%"]
    )
    assert result in ("medium", "low")


def test_confidence_no_warnings_default() -> None:
    """Existing callers pass only spread_summary — default should behave as before."""
    assert confidence_class({"relative_spread": 0.03}) == "high"
    assert confidence_class({"relative_spread": 0.10}) == "medium"
    assert confidence_class({"relative_spread": 0.20}) == "low"


# ---------------------------------------------------------------------------
# extrapolation_status tests
# ---------------------------------------------------------------------------


def test_extrapolation_status_in_range() -> None:
    state = make_state(re=10000)
    meta = make_meta(re_min=3000, re_max=50000)
    status = extrapolation_status(state, meta)
    assert status["extrapolated"] is False
    assert len(status["warnings"]) == 0


def test_extrapolation_status_above_re_max() -> None:
    state = make_state(re=100000)
    meta = make_meta(re_min=3000, re_max=50000)
    status = extrapolation_status(state, meta)
    assert status["extrapolated"] is True
    assert len(status["warnings"]) > 0
    assert status["re_fraction"] is not None
    assert status["re_fraction"] > 1.0


def test_extrapolation_status_below_re_min() -> None:
    state = make_state(re=1000)
    meta = make_meta(re_min=3000, re_max=50000)
    status = extrapolation_status(state, meta)
    assert status["extrapolated"] is True
    assert len(status["warnings"]) > 0


def test_extrapolation_status_no_bounds() -> None:
    state = make_state(re=10000)
    meta = make_meta(re_min=None, re_max=None, pr_min=None)
    status = extrapolation_status(state, meta)
    assert status["extrapolated"] is False
    assert status["re_fraction"] is None
    assert len(status["warnings"]) == 0


def test_extrapolation_status_re_fraction_at_max() -> None:
    """re_fraction = re / re_max when above range."""
    state = make_state(re=100000)
    meta = make_meta(re_min=3000, re_max=50000)
    status = extrapolation_status(state, meta)
    assert status["re_fraction"] == pytest.approx(100000 / 50000, rel=1e-3)


# ---------------------------------------------------------------------------
# UncertaintyEngine tests
# ---------------------------------------------------------------------------


def _make_meta_with_pct(
    pct: float | None,
    re_min: float | None = 3000.0,
    re_max: float | None = 50000.0,
    pr_min: float | None = 0.5,
    pr_max: float | None = 20.0,
) -> CorrelationMetadata:
    validity: dict = {}
    if re_min is not None:
        validity["re_min"] = re_min
    if re_max is not None:
        validity["re_max"] = re_max
    if pr_min is not None:
        validity["pr_min"] = pr_min
    if pr_max is not None:
        validity["pr_max"] = pr_max
    return CorrelationMetadata(
        key="internal.test",
        family="convection_internal",
        title="Test",
        output="Nu",
        literature_uncertainty_pct=pct,
        validity=validity,
        source={"year": 1976},
    )


def _make_eval(value: float = 100.0) -> EvaluationResult:
    return EvaluationResult(
        key="internal.test", output_name="Nu", value=value, metadata={}
    )


def test_band_nominal() -> None:
    """Valid pct, in-range state → correct h_low and h_high."""
    state = make_state(re=10000.0)
    meta = _make_meta_with_pct(pct=10.0)
    ev = _make_eval(value=100.0)
    engine = UncertaintyEngine()
    results = engine.compute(state, [ev], [meta])
    r = results[0]
    # h = Nu * k / L = 100 * 0.6 / 0.025 = 2400.0
    expected_h = 100.0 * 0.6 / 0.025
    assert r.h == pytest.approx(expected_h)
    assert r.h_low == pytest.approx(expected_h * 0.90)
    assert r.h_high == pytest.approx(expected_h * 1.10)
    assert r.note == ""
    assert r.extrapolated is False
    assert r.uncertainty_pct == 10.0


def test_band_none_when_no_pct() -> None:
    """literature_uncertainty_pct=None → h_low/h_high are None, note present."""
    state = make_state(re=10000.0)
    meta = _make_meta_with_pct(pct=None)
    ev = _make_eval(value=100.0)
    engine = UncertaintyEngine()
    results = engine.compute(state, [ev], [meta])
    r = results[0]
    assert r.h_low is None
    assert r.h_high is None
    assert "No stated uncertainty" in r.note
    assert r.uncertainty_pct is None


def test_band_zero_pct_suppressed() -> None:
    """pct=0 is not physically meaningful → band suppressed."""
    state = make_state(re=10000.0)
    meta = _make_meta_with_pct(pct=0.0)
    ev = _make_eval(value=100.0)
    results = UncertaintyEngine().compute(state, [ev], [meta])
    r = results[0]
    assert r.h_low is None
    assert r.h_high is None
    assert "≤0%" in r.note


def test_band_negative_pct_suppressed() -> None:
    """pct<0 → band suppressed."""
    state = make_state(re=10000.0)
    meta = _make_meta_with_pct(pct=-5.0)
    ev = _make_eval(value=100.0)
    results = UncertaintyEngine().compute(state, [ev], [meta])
    r = results[0]
    assert r.h_low is None
    assert r.h_high is None
    assert "≤0%" in r.note


def test_band_clamped_above_100pct() -> None:
    """pct>100 → band computed but h_low clamped to 0, note explains."""
    state = make_state(re=10000.0)
    meta = _make_meta_with_pct(pct=120.0)
    ev = _make_eval(value=100.0)
    results = UncertaintyEngine().compute(state, [ev], [meta])
    r = results[0]
    # h_low would be h * (1 - 1.20) = negative → clamped to 0
    assert r.h_low == pytest.approx(0.0)
    assert r.h_high is not None
    assert "clamped" in r.note


def test_band_suppressed_re_above() -> None:
    """Re > re_max → extrapolated flag True, band suppressed."""
    state = make_state(re=100000.0)  # above re_max=50000
    meta = _make_meta_with_pct(pct=10.0)
    ev = _make_eval(value=100.0)
    results = UncertaintyEngine().compute(state, [ev], [meta])
    r = results[0]
    assert r.extrapolated is True
    assert r.h_low is None
    assert r.h_high is None
    assert "outside validity range" in r.note


def test_band_suppressed_re_below() -> None:
    """Re < re_min → extrapolated flag True, band suppressed."""
    state = make_state(re=100.0)  # below re_min=3000
    meta = _make_meta_with_pct(pct=10.0)
    ev = _make_eval(value=100.0)
    results = UncertaintyEngine().compute(state, [ev], [meta])
    r = results[0]
    assert r.extrapolated is True
    assert r.h_low is None


def test_band_suppressed_pr_above() -> None:
    """Pr > pr_max → extrapolated, band suppressed.

    Default state has Pr ≈ 6.97 (k=0.6, cp=4180, mu=0.001).
    Setting pr_max=1.0 puts the state outside range.
    """
    state = make_state(re=10000.0)
    meta = _make_meta_with_pct(pct=10.0, pr_max=1.0)
    ev = _make_eval(value=100.0)
    results = UncertaintyEngine().compute(state, [ev], [meta])
    r = results[0]
    assert r.extrapolated is True
    assert r.h_low is None


def test_band_suppressed_pr_below() -> None:
    """Pr < pr_min → extrapolated, band suppressed.

    Default state has Pr ≈ 6.97. Setting pr_min=10.0 puts it below range.
    """
    state = make_state(re=10000.0)
    meta = _make_meta_with_pct(pct=10.0, pr_min=10.0, pr_max=None)
    ev = _make_eval(value=100.0)
    results = UncertaintyEngine().compute(state, [ev], [meta])
    r = results[0]
    assert r.extrapolated is True
    assert r.h_low is None


def test_band_suppressed_zero_value() -> None:
    """Evaluated value ≤ 0 → h ≤ 0 → band suppressed."""
    state = make_state(re=10000.0)
    meta = _make_meta_with_pct(pct=10.0)
    ev = _make_eval(value=0.0)
    results = UncertaintyEngine().compute(state, [ev], [meta])
    r = results[0]
    assert r.h_low is None
    assert r.h_high is None
    assert "≤ 0" in r.note


def test_empty_evaluations() -> None:
    """compute() with empty list returns empty list without error."""
    state = make_state()
    engine = UncertaintyEngine()
    results = engine.compute(state, [], [])
    assert results == []
