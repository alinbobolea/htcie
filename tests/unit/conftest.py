"""Shared pytest fixtures for htcie unit tests."""

from __future__ import annotations

import pytest

from htcie.core.explain import Explanation
from htcie.core.state import (
    BoundaryConditions,
    EngineeringState,
    FlowState,
    FluidProperties,
    Geometry,
)
from htcie.reports.schema import HtcieReport


@pytest.fixture()
def sample_state() -> EngineeringState:
    return EngineeringState(
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


@pytest.fixture()
def sample_report(sample_state: EngineeringState) -> HtcieReport:
    explanation = Explanation(
        best_method="internal.gnielinski",
        best_score=0.8,
        score_breakdown={"validity_fit": 0.9, "geometry_match": 1.0},
        why_applicable=["Applicable for Re=10000"],
        why_others_excluded=[("internal.dittus_boelter", "Re too low")],
        key_assumptions=["Smooth tube"],
        confidence_class="high",
        extrapolation_warnings=[],
        recommendation_note="Use internal.gnielinski.",
    )
    return HtcieReport(
        input_state=sample_state,
        derived={
            "reynolds": sample_state.reynolds,
            "prandtl": sample_state.prandtl,
            "graetz": None,
            "entry_length_ratio": None,
            "pitch_ratio_transverse": None,
            "pitch_ratio_longitudinal": None,
        },
        applicable=["internal.gnielinski"],
        excluded=[{"key": "internal.dittus_boelter", "reason": "Re too low"}],
        evaluations=[
            {
                "key": "internal.gnielinski",
                "value": 61.3,
                "metadata": {},
                "h": 3678.0,
                "h_low": 3310.2,
                "h_high": 4045.8,
                "uncertainty_pct": 10.0,
                "uncertainty_note": "Validated for smooth tubes",
            }
        ],
        ranking=[
            {
                "key": "internal.gnielinski",
                "score": 0.8,
                "breakdown": {"validity_fit": 0.9, "geometry_match": 1.0},
            }
        ],
        spread={"count": 1, "mean": 61.3, "stdev": 0.0, "relative_spread": None},
        confidence="high",
        explanation=explanation,
        scoring_weights_version="v1",
    )
