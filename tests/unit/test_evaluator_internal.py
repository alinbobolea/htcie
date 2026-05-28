"""Tests for the EvaluationEngine with internal convection correlations."""

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


def make_internal_state(
    re_approx: float,
    pr_approx: float = 0.7,
    wall_viscosity: float | None = None,
    bulk_temperature: float | None = None,
    wall_temperature: float | None = None,
) -> EngineeringState:
    """Build a circular_tube EngineeringState targeting the given Re and Pr.

    Uses air-like thermal properties and adjusts velocity to hit re_approx.
    Sets k/cp to achieve pr_approx.
    """
    # Air-like base: rho=1.2, D=0.02
    rho = 1.2
    D = 0.02
    # Choose mu and k/cp to hit Pr
    # Pr = cp * mu / k; pick k=0.026, cp=1005 → mu_for_pr = pr * k / cp
    k = 0.026
    cp = 1005.0
    mu = pr_approx * k / cp
    # velocity for desired Re: Re = rho * v * D / mu → v = Re * mu / (rho * D)
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
            geometry_type="circular_tube",
            characteristic_length=D,
            hydraulic_diameter=D,
        ),
        boundary=BoundaryConditions(
            boundary_type="constant_wall_temperature",
            bulk_temperature=bulk_temperature,
            wall_temperature=wall_temperature,
        ),
        flow=FlowState(velocity=v),
    )


@pytest.fixture(scope="module")
def registry() -> CorrelationRegistry:
    return _load_registry()


@pytest.fixture(scope="module")
def engine() -> EvaluationEngine:
    return EvaluationEngine()


class TestDittusBoelter:
    def test_heating_re20000_pr07(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Nu = 0.023 * 20000^0.8 * 0.7^0.4 ≈ 55.0."""
        state = make_internal_state(re_approx=20000.0, pr_approx=0.7)
        method = registry.get("internal.dittus_boelter")
        result = engine.evaluate(state, method)
        expected = 0.023 * 20000**0.8 * 0.7**0.4
        assert result.value == pytest.approx(expected, rel=0.02)

    def test_cooling_uses_n03_exponent(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """When T_bulk > T_wall (cooling), n=0.3 is used.

        For Pr > 1, Pr^0.3 < Pr^0.4 so cooling gives a lower Nu than heating.
        We use Pr ≈ 3.0 to confirm this direction reliably.
        """
        state_heating = make_internal_state(
            re_approx=20000.0,
            pr_approx=3.0,
            bulk_temperature=300.0,
            wall_temperature=400.0,
        )
        state_cooling = make_internal_state(
            re_approx=20000.0,
            pr_approx=3.0,
            bulk_temperature=400.0,
            wall_temperature=300.0,
        )
        method = registry.get("internal.dittus_boelter")
        nu_heating = engine.evaluate(state_heating, method).value
        nu_cooling = engine.evaluate(state_cooling, method).value
        # For Pr > 1: Pr^0.4 > Pr^0.3 → heating (n=0.4) gives higher Nu
        assert nu_cooling < nu_heating

    def test_returns_positive_float(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        state = make_internal_state(re_approx=15000.0, pr_approx=3.0)
        method = registry.get("internal.dittus_boelter")
        result = engine.evaluate(state, method)
        assert result.value > 0.0
        assert result.key == "internal.dittus_boelter"


class TestGnielinski:
    def test_re10000_pr07(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Gnielinski at Re=10000, Pr=0.7: expected Nu ≈ 29.8."""
        from math import log

        state = make_internal_state(re_approx=10000.0, pr_approx=0.7)
        method = registry.get("internal.gnielinski")
        result = engine.evaluate(state, method)
        re = state.reynolds
        pr = state.prandtl
        f = (0.790 * log(re) - 1.64) ** -2
        expected = (
            (f / 8)
            * (re - 1000)
            * pr
            / (1 + 12.7 * (f / 8) ** 0.5 * (pr ** (2 / 3) - 1))
        )
        assert result.value == pytest.approx(expected, rel=0.02)

    def test_raises_for_re_below_3000(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Gnielinski raises ValueError when Re < 3000."""
        state = make_internal_state(re_approx=2000.0, pr_approx=0.7)
        method = registry.get("internal.gnielinski")
        with pytest.raises(ValueError, match="Re"):
            engine.evaluate(state, method)

    def test_evaluates_just_above_re_3000(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Gnielinski evaluates without error at Re just above 3000.

        Previously the guard was 're <= 3000' which meant Re=3001 (and anything
        the YAML re_min=3000 applicability passed) would crash the evaluator.
        """
        state = make_internal_state(re_approx=3001.0, pr_approx=0.7)
        method = registry.get("internal.gnielinski")
        result = engine.evaluate(state, method)
        assert result.value > 0.0


class TestPetukhov:
    def test_re50000_pr07(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Petukhov at Re=50000, Pr=0.7: verify formula against hand calculation."""
        from math import log

        state = make_internal_state(re_approx=50000.0, pr_approx=0.7)
        method = registry.get("internal.petukhov")
        result = engine.evaluate(state, method)
        re = state.reynolds
        pr = state.prandtl
        f = (0.790 * log(re) - 1.64) ** -2
        expected = (
            (f / 8) * re * pr / (1.07 + 12.7 * (f / 8) ** 0.5 * (pr ** (2 / 3) - 1))
        )
        assert result.value == pytest.approx(expected, rel=1e-6)

    def test_returns_positive_float(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        state = make_internal_state(re_approx=100000.0, pr_approx=5.0)
        method = registry.get("internal.petukhov")
        result = engine.evaluate(state, method)
        assert result.value > 0.0
        assert result.key == "internal.petukhov"

    def test_gnielinski_vs_petukhov_ordering(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """At Re=50000, Gnielinski > Petukhov (denominator 1.07 vs 1.0
        lowers Petukhov)."""
        state = make_internal_state(re_approx=50000.0, pr_approx=0.7)
        gn_result = engine.evaluate(state, registry.get("internal.gnielinski"))
        pe_result = engine.evaluate(state, registry.get("internal.petukhov"))
        assert gn_result.value > pe_result.value


class TestSiederTate:
    def test_without_wall_viscosity_returns_positive(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Sieder-Tate without wall_viscosity applies factor=1.0 and returns Nu > 0."""
        state = make_internal_state(
            re_approx=20000.0, pr_approx=0.7, wall_viscosity=None
        )
        method = registry.get("internal.sieder_tate")
        result = engine.evaluate(state, method)
        assert result.value > 0.0
        assert result.metadata["viscosity_ratio_applied"] is False

    def test_with_wall_viscosity_applies_correction(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Sieder-Tate with wall_viscosity records viscosity_ratio_applied=True."""
        mu = make_internal_state(re_approx=20000.0, pr_approx=0.7).fluid.viscosity
        state = make_internal_state(
            re_approx=20000.0, pr_approx=0.7, wall_viscosity=mu * 1.5
        )
        method = registry.get("internal.sieder_tate")
        result = engine.evaluate(state, method)
        assert result.value > 0.0
        assert result.metadata["viscosity_ratio_applied"] is True


class TestLowReExclusion:
    """At Re=100 (far below turbulent threshold), turbulent correlations raise."""

    def test_dittus_boelter_evaluates_at_low_re(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Dittus-Boelter has no Re guard; it computes for any Re > 0."""
        state = make_internal_state(re_approx=100.0, pr_approx=0.7)
        method = registry.get("internal.dittus_boelter")
        # No ValueError is raised; applicability engine handles the guard separately.
        result = engine.evaluate(state, method)
        assert result.value > 0.0

    def test_gnielinski_raises_at_low_re(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Gnielinski explicitly raises ValueError for Re < 3000."""
        state = make_internal_state(re_approx=100.0, pr_approx=0.7)
        method = registry.get("internal.gnielinski")
        with pytest.raises(ValueError):
            engine.evaluate(state, method)


class TestShahLaminar:
    def test_fully_developed_returns_366(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Without developing_length, Shah returns fully-developed Nu=3.66."""
        state = make_internal_state(re_approx=500.0, pr_approx=5.0)
        method = registry.get("internal.shah_laminar")
        result = engine.evaluate(state, method)
        assert result.value == pytest.approx(3.66, rel=1e-6)

    def test_developing_flow_exceeds_366(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """With developing_length set, Shah Nu > 3.66."""
        state = make_internal_state(re_approx=500.0, pr_approx=5.0)
        state = state.model_copy(
            update={
                "flow": FlowState(velocity=state.flow.velocity, developing_length=0.5)
            }
        )
        method = registry.get("internal.shah_laminar")
        result = engine.evaluate(state, method)
        assert result.value > 3.66

    def test_formula_matches_hand_calculation(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Verify Nu against hand-calculated formula."""
        state = make_internal_state(re_approx=500.0, pr_approx=5.0)
        state = state.model_copy(
            update={
                "flow": FlowState(velocity=state.flow.velocity, developing_length=0.5)
            }
        )
        method = registry.get("internal.shah_laminar")
        result = engine.evaluate(state, method)
        D = state.geometry.hydraulic_diameter or state.geometry.characteristic_length
        gz = state.reynolds * state.prandtl * (D / 0.5)
        expected = 3.66 + (0.0668 * gz) / (1 + 0.04 * gz ** (2 / 3))
        assert result.value == pytest.approx(expected, rel=1e-6)


class TestChurchillOzoe:
    def test_cwt_base_nu_without_developing_length(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Without developing_length, Churchill-Ozoe (CWT) returns Nu=3.66."""
        state = make_internal_state(re_approx=300.0, pr_approx=5.0)
        method = registry.get("internal.churchill_ozoe")
        result = engine.evaluate(state, method)
        assert result.value == pytest.approx(3.66, rel=1e-6)

    def test_chf_base_nu_without_developing_length(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """Without developing_length, Churchill-Ozoe (CHF) returns Nu=4.36."""
        state = make_internal_state(re_approx=300.0, pr_approx=5.0)
        state = state.model_copy(
            update={"boundary": BoundaryConditions(boundary_type="constant_heat_flux")}
        )
        method = registry.get("internal.churchill_ozoe")
        result = engine.evaluate(state, method)
        assert result.value == pytest.approx(4.36, rel=1e-6)

    def test_developing_flow_exceeds_base(
        self, registry: CorrelationRegistry, engine: EvaluationEngine
    ) -> None:
        """With developing_length, Nu exceeds the fully-developed base value."""
        state = make_internal_state(re_approx=300.0, pr_approx=5.0)
        state = state.model_copy(
            update={
                "flow": FlowState(velocity=state.flow.velocity, developing_length=1.0)
            }
        )
        method = registry.get("internal.churchill_ozoe")
        result = engine.evaluate(state, method)
        assert result.value > 3.66
