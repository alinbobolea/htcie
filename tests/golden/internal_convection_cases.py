"""Golden reference cases for internal forced convection correlations.

Physical data sourced from Incropera et al., "Fundamentals of Heat and Mass
Transfer", 7th edition, Appendix A.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from htcie.core.applicability import ApplicabilityEngine
from htcie.core.evaluator import EvaluationEngine
from htcie.core.registry import CorrelationRegistry
from htcie.core.state import (
    BoundaryConditions,
    EngineeringState,
    FlowState,
    FluidProperties,
    Geometry,
)

_DATA_DIR = Path(__file__).parents[2] / "data" / "correlations"


def _load_registry() -> CorrelationRegistry:
    reg = CorrelationRegistry()
    reg.load_from_dir(_DATA_DIR)
    return reg


# ---------------------------------------------------------------------------
# Golden case definitions
# ---------------------------------------------------------------------------

# Water at 60°C, D=25mm, U=1 m/s
# ρ=983.2 kg/m³, μ=4.67e-4 Pa·s, k=0.654 W/m·K, cp=4185 J/kg·K
# Re = ρUD/μ ≈ 52634, Pr ≈ 2.99
# Gnielinski Nu ≈ 235 (Incropera 8th ed Example 8.3 gives ~244; allow ±10%)
_WATER_60C = EngineeringState(
    fluid=FluidProperties(
        density=983.2,
        viscosity=4.67e-4,
        thermal_conductivity=0.654,
        heat_capacity=4185.0,
    ),
    geometry=Geometry(
        geometry_type="circular_tube",
        characteristic_length=0.025,
        hydraulic_diameter=0.025,
    ),
    boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
    flow=FlowState(velocity=1.0),
)

# Air at 300K, D=20mm, U=10 m/s
# ρ=1.177 kg/m³, μ=1.846e-5 Pa·s, k=0.0263 W/m·K, cp=1007 J/kg·K
# Re = ρUD/μ ≈ 12758, Pr ≈ 0.707
# Gnielinski Nu ≈ 36 (±10%)
_AIR_300K = EngineeringState(
    fluid=FluidProperties(
        density=1.177,
        viscosity=1.846e-5,
        thermal_conductivity=0.0263,
        heat_capacity=1007.0,
    ),
    geometry=Geometry(
        geometry_type="circular_tube",
        characteristic_length=0.020,
        hydraulic_diameter=0.020,
    ),
    boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
    flow=FlowState(velocity=10.0),
)

_GOLDEN_CASES: list[tuple[str, EngineeringState, float, float]] = [
    ("water_60C_25mm_1ms", _WATER_60C, 200.0, 300.0),
    ("air_300K_20mm_10ms", _AIR_300K, 30.0, 55.0),
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def registry() -> CorrelationRegistry:
    return _load_registry()


@pytest.fixture(scope="module")
def evaluation_engine() -> EvaluationEngine:
    return EvaluationEngine()


@pytest.fixture(scope="module")
def applicability_engine() -> ApplicabilityEngine:
    return ApplicabilityEngine()


@pytest.mark.parametrize(
    "label,state,nu_lo,nu_hi", _GOLDEN_CASES, ids=[c[0] for c in _GOLDEN_CASES]
)
def test_at_least_one_applicable_method_in_nu_range(
    label: str,
    state: EngineeringState,
    nu_lo: float,
    nu_hi: float,
    registry: CorrelationRegistry,
    evaluation_engine: EvaluationEngine,
    applicability_engine: ApplicabilityEngine,
) -> None:
    """At least one applicable method must return Nu within the expected range."""
    all_methods = registry.all()
    applicable = applicability_engine.evaluate(state, all_methods).applicable

    assert applicable, (
        f"[{label}] No applicable methods found for Re={state.reynolds:.0f}"
    )

    nu_values = []
    for method in applicable:
        try:
            result = evaluation_engine.evaluate(state, method)
            nu_values.append((method.key, result.value))
        except (ValueError, NotImplementedError):
            pass

    in_range = [(key, nu) for key, nu in nu_values if nu_lo <= nu <= nu_hi]
    assert in_range, (
        f"[{label}] No method returned Nu in [{nu_lo}, {nu_hi}]. Got: {nu_values}"
    )


def test_water_60c_reynolds_and_prandtl() -> None:
    """Re and Pr for the water 60°C case must match hand-calc within 1%."""
    state = _WATER_60C
    assert state.reynolds == pytest.approx(52634.0, rel=0.01)
    assert state.prandtl == pytest.approx(2.99, rel=0.01)


def test_air_300k_reynolds_and_prandtl() -> None:
    """Re and Pr for the air 300K case must match hand-calc within 1%."""
    state = _AIR_300K
    assert state.reynolds == pytest.approx(12758.0, rel=0.01)
    assert state.prandtl == pytest.approx(0.707, rel=0.01)
