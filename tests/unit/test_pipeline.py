"""Tests for the shared evaluation pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from htcie.core.pipeline import run_evaluation
from htcie.core.registry import CorrelationRegistry
from htcie.core.state import (
    BoundaryConditions,
    EngineeringState,
    FlowState,
    FluidProperties,
    Geometry,
)
from htcie.reports.schema import HtcieReport

_DATA_DIR = Path(__file__).parents[2] / "data" / "correlations"


@pytest.fixture(scope="module")
def registry() -> CorrelationRegistry:
    reg = CorrelationRegistry()
    reg.load_from_dir(_DATA_DIR)
    return reg


def _water_tube_state() -> EngineeringState:
    """Turbulent water in a tube — several methods should apply."""
    return EngineeringState(
        fluid=FluidProperties(
            density=983.0,
            viscosity=4.67e-4,
            thermal_conductivity=0.654,
            heat_capacity=4185.0,
        ),
        geometry=Geometry(
            geometry_type="circular_tube",
            characteristic_length=0.02,
            hydraulic_diameter=0.02,
        ),
        boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
        flow=FlowState(velocity=0.5),
    )


def test_run_evaluation_returns_report(registry: CorrelationRegistry) -> None:
    state = _water_tube_state()
    report = run_evaluation(state, registry)
    assert isinstance(report, HtcieReport)


def test_run_evaluation_report_has_ranking(registry: CorrelationRegistry) -> None:
    state = _water_tube_state()
    report = run_evaluation(state, registry)
    assert report is not None
    assert len(report.ranking) >= 1


def test_run_evaluation_report_is_serializable(
    registry: CorrelationRegistry,
) -> None:
    """report.to_dict() must return a JSON-serializable dict."""
    import json

    state = _water_tube_state()
    report = run_evaluation(state, registry)
    assert report is not None
    serialized = json.dumps(report.to_dict())
    assert len(serialized) > 100


def test_run_evaluation_report_has_uncertainty_fields(
    registry: CorrelationRegistry,
) -> None:
    """Each evaluation dict must contain h, h_low, h_high, uncertainty_pct, uncertainty_note."""
    state = _water_tube_state()
    report = run_evaluation(state, registry)
    assert report is not None
    for ev in report.evaluations:
        assert "uncertainty_pct" in ev, f"{ev['key']} missing uncertainty_pct"
        assert "h" in ev, f"{ev['key']} missing h"
        assert "h_low" in ev, f"{ev['key']} missing h_low"
        assert "h_high" in ev, f"{ev['key']} missing h_high"
        assert "uncertainty_note" in ev, f"{ev['key']} missing uncertainty_note"
        # h must always be a positive float (valid turbulent state)
        assert isinstance(ev["h"], float) and ev["h"] > 0


def test_run_evaluation_scoring_weights_version(
    registry: CorrelationRegistry,
) -> None:
    """scoring_weights_version must match the current DEFAULT_WEIGHTS version."""
    state = _water_tube_state()
    report = run_evaluation(state, registry)
    assert report is not None
    assert report.scoring_weights_version == "v1.1"


def test_run_evaluation_no_applicable_returns_none(
    registry: CorrelationRegistry,
) -> None:
    """Re in transitional regime (2300 < Re < 3000) — no correlations applicable."""
    # Re ≈ 2700: above laminar max (2300) but below all turbulent mins (3000+)
    state = EngineeringState(
        fluid=FluidProperties(
            density=983.0,
            viscosity=4.67e-4,
            thermal_conductivity=0.654,
            heat_capacity=4185.0,
        ),
        geometry=Geometry(
            geometry_type="circular_tube",
            characteristic_length=0.02,
            hydraulic_diameter=0.02,
        ),
        boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
        flow=FlowState(velocity=0.064),
    )
    result = run_evaluation(state, registry)
    assert result is None
