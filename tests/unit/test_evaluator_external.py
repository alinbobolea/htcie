"""Tests for the EvaluationEngine with external convection correlations."""

from __future__ import annotations

from pathlib import Path

import pytest

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


def make_cylinder_state(
    re_approx: float,
    pr_approx: float = 0.7,
    wall_viscosity: float | None = None,
) -> EngineeringState:
    """Build a cylinder_crossflow EngineeringState targeting the given Re and Pr."""
    rho = 1.2
    D = 0.02
    k = 0.026
    cp = 1005.0
    mu = pr_approx * k / cp
    v = re_approx * mu / (rho * D)

    return EngineeringState(
        fluid=FluidProperties(
            density=rho,
            viscosity=mu,
            thermal_conductivity=k,
            heat_capacity=cp,
            wall_viscosity=wall_viscosity,
        ),
        geometry=Geometry(
            geometry_type="cylinder_crossflow",
            characteristic_length=D,
        ),
        boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
        flow=FlowState(velocity=v),
    )


def make_flat_plate_state(
    re_approx: float,
    pr_approx: float = 0.7,
) -> EngineeringState:
    """Build a flat_plate EngineeringState targeting the given Re and Pr."""
    rho = 1.2
    L = 1.0
    k = 0.026
    cp = 1005.0
    mu = pr_approx * k / cp
    v = re_approx * mu / (rho * L)

    return EngineeringState(
        fluid=FluidProperties(
            density=rho,
            viscosity=mu,
            thermal_conductivity=k,
            heat_capacity=cp,
        ),
        geometry=Geometry(
            geometry_type="flat_plate",
            characteristic_length=L,
        ),
        boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
        flow=FlowState(velocity=v),
    )


@pytest.fixture(scope="module")
def registry() -> CorrelationRegistry:
    return _load_registry()


@pytest.fixture(scope="module")
def engine() -> EvaluationEngine:
    return EvaluationEngine()


class TestChurchillBernstein:
    def test_re40000_pr07(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Churchill-Bernstein at Re=40000, Pr=0.7: expected Nu ≈ 119."""
        state = make_cylinder_state(re_approx=40000.0, pr_approx=0.7)
        method = registry.get("external.churchill_bernstein")
        result = engine.evaluate(state, method)
        # Formula: Nu = 0.3 + (0.62*Re^0.5*Pr^(1/3)) / (1+(0.4/Pr)^(2/3))^0.25
        #               * (1+(Re/282000)^(5/8))^(4/5)
        re = state.reynolds
        pr = state.prandtl
        expected = 0.3 + (
            (0.62 * re**0.5 * pr ** (1 / 3))
            / (1 + (0.4 / pr) ** (2 / 3)) ** 0.25
            * (1 + (re / 282000) ** (5 / 8)) ** (4 / 5)
        )
        assert result.value == pytest.approx(expected, rel=0.02)
        # Within 5% of ~124 (Incropera reference value — formula gives ~119)
        assert 100 < result.value < 150

    def test_returns_positive_float(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        state = make_cylinder_state(re_approx=10000.0, pr_approx=0.7)
        method = registry.get("external.churchill_bernstein")
        result = engine.evaluate(state, method)
        assert result.value > 0.0
        assert result.key == "external.churchill_bernstein"


class TestPohlhausenPlate:
    def test_re100000_pr07(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Pohlhausen at Re=100000, Pr=0.7: Nu = 0.664*Re^0.5*Pr^(1/3) ≈ 186.4."""
        state = make_flat_plate_state(re_approx=100000.0, pr_approx=0.7)
        method = registry.get("external.pohlhausen_plate")
        result = engine.evaluate(state, method)
        re = state.reynolds
        pr = state.prandtl
        expected = 0.664 * re**0.5 * pr ** (1 / 3)
        assert result.value == pytest.approx(expected, rel=0.02)
        assert abs(result.value - 186.4) / 186.4 < 0.02

    def test_raises_for_turbulent_re(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Pohlhausen raises ValueError when Re >= 5e5 (turbulent regime)."""
        state = make_flat_plate_state(re_approx=600000.0, pr_approx=0.7)
        method = registry.get("external.pohlhausen_plate")
        with pytest.raises(ValueError, match="Re"):
            engine.evaluate(state, method)


class TestZukauskasCylinder:
    def test_re40000_pr07_returns_positive(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Žukauskas cylinder at Re=40000, Pr=0.7 should return a positive Nu."""
        state = make_cylinder_state(re_approx=40000.0, pr_approx=0.7)
        method = registry.get("external.zukauskas_cylinder")
        result = engine.evaluate(state, method)
        assert result.value > 0.0
        assert result.key == "external.zukauskas_cylinder"

    def test_without_wall_viscosity(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Žukauskas without wall_viscosity uses correction factor 1.0."""
        state = make_cylinder_state(
            re_approx=40000.0, pr_approx=0.7, wall_viscosity=None
        )
        method = registry.get("external.zukauskas_cylinder")
        result = engine.evaluate(state, method)
        assert result.metadata["wall_prandtl_applied"] is False

    def test_formula_matches_hand_calc(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Žukauskas at Re=40000 uses C=0.26, m=0.6 from the 1000-200000 band.

        Pr=0.7 <= 10 so Pr exponent n=0.37 per Incropera Eq 7.53.
        """
        state = make_cylinder_state(re_approx=40000.0, pr_approx=0.7)
        method = registry.get("external.zukauskas_cylinder")
        result = engine.evaluate(state, method)
        re = state.reynolds
        pr = state.prandtl
        # Re=40000 falls in [1000, 200000): C=0.26, m=0.6; Pr=0.7 <= 10 → n=0.37
        expected = 0.26 * re**0.6 * pr**0.37
        assert result.value == pytest.approx(expected, rel=0.02)

    def test_pr_exponent_0p36_for_pr_gt_10(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Žukauskas uses n=0.36 for Pr > 10 (e.g. oil, Pr=50)."""
        state = make_cylinder_state(re_approx=40000.0, pr_approx=50.0)
        method = registry.get("external.zukauskas_cylinder")
        result = engine.evaluate(state, method)
        re = state.reynolds
        pr = state.prandtl
        expected = 0.26 * re**0.6 * pr**0.36
        assert result.value == pytest.approx(expected, rel=0.02)
        assert result.metadata["pr_exponent_n"] == pytest.approx(0.36)

    def test_pr_exponent_0p37_for_pr_le_10(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Žukauskas uses n=0.37 for Pr <= 10 (e.g. air, Pr=0.7)."""
        state = make_cylinder_state(re_approx=40000.0, pr_approx=0.7)
        method = registry.get("external.zukauskas_cylinder")
        result = engine.evaluate(state, method)
        assert result.metadata["pr_exponent_n"] == pytest.approx(0.37)


class TestHilpert:
    def test_returns_positive_float(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        state = make_cylinder_state(re_approx=5000.0, pr_approx=0.7)
        method = registry.get("external.hilpert")
        result = engine.evaluate(state, method)
        assert result.value > 0.0

    def test_raises_for_out_of_range_re(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Hilpert raises ValueError for Re outside [0.4, 400000)."""
        state = make_cylinder_state(re_approx=500000.0, pr_approx=0.7)
        method = registry.get("external.hilpert")
        with pytest.raises(ValueError):
            engine.evaluate(state, method)


class TestTurbulentPlate:
    def test_formula_matches_hand_calculation(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Nu = (0.037 * Re^0.8 - 871) * Pr^(1/3) — mixed boundary layer."""
        state = make_flat_plate_state(re_approx=1e6, pr_approx=0.71)
        method = registry.get("external.turbulent_plate")
        result = engine.evaluate(state, method)
        re = state.reynolds
        pr = state.prandtl
        expected = (0.037 * re**0.8 - 871) * pr ** (1 / 3)
        assert result.value == pytest.approx(expected, rel=1e-6)

    def test_returns_positive_nu(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        state = make_flat_plate_state(re_approx=5e6, pr_approx=0.71)
        method = registry.get("external.turbulent_plate")
        result = engine.evaluate(state, method)
        assert result.value > 0.0
        assert result.output_name == "Nu"
