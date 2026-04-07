"""Tests for ApplicabilityEngine filtering logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from htcie.core.applicability import ApplicabilityEngine
from htcie.core.registry import CorrelationRegistry
from htcie.core.state import (
    BoundaryConditions,
    EngineeringState,
    FlowState,
    FluidProperties,
    Geometry,
)

_DATA_DIR = Path(__file__).parents[2] / "data" / "correlations"


@pytest.fixture(scope="module")
def registry() -> CorrelationRegistry:
    reg = CorrelationRegistry()
    reg.load_from_dir(_DATA_DIR)
    return reg


@pytest.fixture
def engine() -> ApplicabilityEngine:
    return ApplicabilityEngine()


def _tube_state(
    re_approx: float = 10_000.0, pr_approx: float = 4.0
) -> EngineeringState:
    """Build a circular_tube state targeting the given Re and Pr."""
    rho = 1000.0
    D = 0.01
    k = 0.6
    cp = 4182.0
    mu = pr_approx * k / cp
    v = re_approx * mu / (rho * D)
    return EngineeringState(
        fluid=FluidProperties(
            density=rho,
            viscosity=mu,
            thermal_conductivity=k,
            heat_capacity=cp,
        ),
        geometry=Geometry(geometry_type="circular_tube", characteristic_length=D),
        boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
        flow=FlowState(velocity=v),
    )


def test_applicable_methods_returned_for_valid_state(
    engine: ApplicabilityEngine, registry: CorrelationRegistry
) -> None:
    state = _tube_state()
    result = engine.evaluate(state, registry.all())
    assert len(result.applicable) >= 1


def test_low_re_excluded_with_reason(
    engine: ApplicabilityEngine, registry: CorrelationRegistry
) -> None:
    state = _tube_state(re_approx=10.0)
    result = engine.evaluate(state, registry.all())
    reasons = [reason for _, reason in result.excluded]
    assert any("Reynolds" in r or "Re" in r for r in reasons), reasons


def test_geometry_mismatch_excludes_internal_methods(
    engine: ApplicabilityEngine, registry: CorrelationRegistry
) -> None:
    """Internal (circular_tube) correlations must not apply to cylinder_crossflow."""
    state = _tube_state()
    cylinder_state = state.model_copy(
        update={
            "geometry": Geometry(
                geometry_type="cylinder_crossflow",
                characteristic_length=0.01,
            )
        }
    )
    result = engine.evaluate(cylinder_state, registry.all())
    applicable_keys = {m.key for m in result.applicable}
    internal_keys = {
        "internal.dittus_boelter",
        "internal.gnielinski",
        "internal.petukhov",
    }
    assert internal_keys.isdisjoint(applicable_keys), (
        f"Internal methods must not apply to cylinder: "
        f"{applicable_keys & internal_keys}"
    )


def test_excluded_entries_are_tuples_with_meta_and_reason(
    engine: ApplicabilityEngine, registry: CorrelationRegistry
) -> None:
    state = _tube_state(re_approx=10.0)
    result = engine.evaluate(state, registry.all())
    for meta, reason in result.excluded:
        assert meta.key, "Excluded meta must have a key"
        assert isinstance(reason, str) and reason, "Reason must be a non-empty string"


def test_applicable_entries_have_metadata(
    engine: ApplicabilityEngine, registry: CorrelationRegistry
) -> None:
    state = _tube_state()
    result = engine.evaluate(state, registry.all())
    for meta in result.applicable:
        assert meta.key
        assert meta.family
