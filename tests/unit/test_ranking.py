"""Tests for the RankingEngine scoring and determinism."""

from __future__ import annotations

from pathlib import Path

import pytest

from htcie.core.applicability import ApplicabilityEngine
from htcie.core.ranking import (
    RE_LAMINAR_MAX,
    RE_PLATE_TURBULENT,
    RE_TRANSITION_MAX,
    RankingEngine,
)
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


def make_tube_state(re_approx: float, pr_approx: float = 0.7) -> EngineeringState:
    """Build a circular_tube EngineeringState targeting the given Re and Pr."""
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
        ),
        geometry=Geometry(
            geometry_type="circular_tube",
            characteristic_length=D,
            hydraulic_diameter=D,
        ),
        boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
        flow=FlowState(velocity=v),
    )


@pytest.fixture(scope="module")
def registry() -> CorrelationRegistry:
    return _load_registry()


@pytest.fixture(scope="module")
def engine() -> RankingEngine:
    return RankingEngine()


class TestDeterminism:
    def test_identical_results_on_repeated_calls(
        self, registry: CorrelationRegistry, engine: RankingEngine
    ) -> None:
        """rank() called twice with the same inputs must return identical results."""
        state = make_tube_state(re_approx=20000.0)
        methods = registry.by_family("convection_internal")

        first = engine.rank(state, methods)
        second = engine.rank(state, methods)

        assert len(first) == len(second)
        for a, b in zip(first, second):
            assert a.key == b.key
            assert a.score == b.score
            assert a.breakdown == b.breakdown


class TestScoreRange:
    def test_all_scores_in_unit_interval(
        self, registry: CorrelationRegistry, engine: RankingEngine
    ) -> None:
        """All ranked scores must lie in [0, 1]."""
        state = make_tube_state(re_approx=20000.0)
        methods = registry.all()
        ranked = engine.rank(state, methods)

        for candidate in ranked:
            assert 0.0 <= candidate.score <= 1.0, (
                f"{candidate.key} has score {candidate.score} outside [0, 1]"
            )

    def test_scores_in_unit_interval_with_extreme_re(
        self, registry: CorrelationRegistry, engine: RankingEngine
    ) -> None:
        """Scores must be clamped to [0, 1] even for extreme Re (far outside validity).

        Exercises the extrapolation penalty path that can otherwise produce
        negative raw totals before clamping.
        """
        state = make_tube_state(re_approx=1e9)
        methods = registry.all()
        ranked = engine.rank(state, methods)

        for candidate in ranked:
            assert 0.0 <= candidate.score <= 1.0, (
                f"{candidate.key} has score {candidate.score} outside [0, 1]"
                " at Re=1e9 (extreme extrapolation)"
            )


class TestGnielinskiVsDittusBoelterAtRe5000:
    def test_gnielinski_ranked_above_or_dittus_boelter_excluded(
        self, registry: CorrelationRegistry, engine: RankingEngine
    ) -> None:
        """At Re≈5000, Gnielinski is valid but Dittus-Boelter requires re_min=10000.

        Dittus-Boelter must be excluded OR Gnielinski must rank above it.
        """
        state = make_tube_state(re_approx=5000.0)
        all_methods = registry.all()

        applicability = ApplicabilityEngine().evaluate(state, all_methods)
        excluded_keys = {m.key for m, _ in applicability.excluded}

        if "internal.dittus_boelter" in excluded_keys:
            # Dittus-Boelter is filtered out — test passes
            assert "internal.gnielinski" not in excluded_keys
        else:
            # Both are applicable; Gnielinski must rank higher
            ranked = engine.rank(state, applicability.applicable)
            keys = [c.key for c in ranked]
            assert "internal.gnielinski" in keys
            g_pos = keys.index("internal.gnielinski")
            db_pos = keys.index("internal.dittus_boelter")
            assert g_pos < db_pos, (
                f"Gnielinski (pos {g_pos}) should rank above"
                f" Dittus-Boelter (pos {db_pos}) at Re=5000"
            )

    def test_dittus_boelter_excluded_at_re5000(
        self, registry: CorrelationRegistry
    ) -> None:
        """Applicability engine must exclude Dittus-Boelter at Re≈5000."""
        state = make_tube_state(re_approx=5000.0)
        methods = registry.all()
        result = ApplicabilityEngine().evaluate(state, methods)
        excluded_keys = {m.key for m, _ in result.excluded}
        assert "internal.dittus_boelter" in excluded_keys

    def test_gnielinski_applicable_at_re5000(
        self, registry: CorrelationRegistry
    ) -> None:
        """Applicability engine must include Gnielinski (re_min=3000) at Re≈5000."""
        state = make_tube_state(re_approx=5000.0)
        methods = registry.all()
        result = ApplicabilityEngine().evaluate(state, methods)
        applicable_keys = {m.key for m in result.applicable}
        assert "internal.gnielinski" in applicable_keys


class TestBreakdownFactors:
    def test_breakdown_contains_expected_keys(
        self, registry: CorrelationRegistry, engine: RankingEngine
    ) -> None:
        """Each RankedCandidate breakdown must contain all scoring factor keys."""
        state = make_tube_state(re_approx=20000.0)
        methods = registry.by_family("convection_internal")
        ranked = engine.rank(state, methods)

        expected_keys = {
            "validity_fit",
            "geometry_match",
            "regime_match",
            "boundary_match",
            "correction_score",
            "pedigree",
            "uncertainty_score",
            "extrapolation_penalty",
        }
        for candidate in ranked:
            assert expected_keys == set(candidate.breakdown.keys()), (
                f"{candidate.key} breakdown missing keys"
            )

    def test_weights_version_recorded(
        self, registry: CorrelationRegistry, engine: RankingEngine
    ) -> None:
        state = make_tube_state(re_approx=20000.0)
        methods = registry.by_family("convection_internal")
        ranked = engine.rank(state, methods)
        for candidate in ranked:
            assert candidate.weights_version == "v1.1"


def test_regime_constants_are_named() -> None:
    """Re regime classification thresholds must be exported named constants."""
    assert RE_LAMINAR_MAX == 2300.0
    assert RE_TRANSITION_MAX == 10_000.0
    assert RE_PLATE_TURBULENT == 5e5


def test_gnielinski_beats_dittus_boelter_uncertainty_weight() -> None:
    """Gnielinski (pct=10%) must rank above Dittus-Boelter (pct=25%) for turbulent
    internal flow at Re=20000 using uncertainty weight alone — not pedigree boost."""
    registry = _load_registry()
    engine = RankingEngine()
    state = make_tube_state(re_approx=20000.0)

    from htcie.core.applicability import ApplicabilityEngine

    app = ApplicabilityEngine().evaluate(state, registry.all())
    ranked = engine.rank(state, app.applicable)

    keys = [c.key for c in ranked]
    assert "internal.gnielinski" in keys
    assert "internal.dittus_boelter" in keys
    g_pos = keys.index("internal.gnielinski")
    db_pos = keys.index("internal.dittus_boelter")
    assert g_pos < db_pos, (
        f"Gnielinski (pos {g_pos}) must rank above Dittus-Boelter (pos {db_pos})"
        " — uncertainty weight should drive this ordering"
    )
