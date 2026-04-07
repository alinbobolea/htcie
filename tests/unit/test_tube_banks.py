"""Unit tests for tube_banks domain correlations."""

from __future__ import annotations

import pytest

from htcie.core.state import (
    BoundaryConditions,
    EngineeringState,
    FlowState,
    FluidProperties,
    Geometry,
)
from htcie.domains.tube_banks import evaluate


# ---------------------------------------------------------------------------
# state helpers
# ---------------------------------------------------------------------------


def _tube_bank_state(
    *,
    velocity: float = 5.0,
    pitch_transverse: float = 0.03,
    pitch_longitudinal: float = 0.04,
    arrangement: str = "staggered",
    diameter: float = 0.02,
    wall_viscosity: float | None = None,
) -> EngineeringState:
    """Air-like fluid in a tube bank at moderate conditions."""
    return EngineeringState(
        fluid=FluidProperties(
            density=1.2,
            viscosity=1.8e-5,
            thermal_conductivity=0.026,
            heat_capacity=1005.0,
            wall_viscosity=wall_viscosity,
        ),
        geometry=Geometry(
            geometry_type="tube_bank",
            characteristic_length=diameter,
            pitch_transverse=pitch_transverse,
            pitch_longitudinal=pitch_longitudinal,
            arrangement=arrangement,
        ),
        boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
        flow=FlowState(velocity=velocity),
    )


# ---------------------------------------------------------------------------
# evaluate() dispatch
# ---------------------------------------------------------------------------


def test_evaluate_dispatches_zukauskas() -> None:
    state = _tube_bank_state()
    result = evaluate("tube_banks.zukauskas", state)
    assert result.key == "tube_banks.zukauskas"


def test_evaluate_dispatches_grimison() -> None:
    state = _tube_bank_state()
    result = evaluate("tube_banks.grimison", state)
    assert result.key == "tube_banks.grimison"


def test_evaluate_raises_for_unknown_key() -> None:
    state = _tube_bank_state()
    with pytest.raises(NotImplementedError):
        evaluate("tube_banks.unknown_correlation", state)


# ---------------------------------------------------------------------------
# arrangement determination
# ---------------------------------------------------------------------------


def test_zukauskas_inline_arrangement() -> None:
    state = _tube_bank_state(arrangement="inline")
    result = evaluate("tube_banks.zukauskas", state)
    assert result.metadata["arrangement"] == "inline"


def test_zukauskas_staggered_arrangement() -> None:
    state = _tube_bank_state(arrangement="staggered")
    result = evaluate("tube_banks.zukauskas", state)
    assert result.metadata["arrangement"] == "staggered"


def test_grimison_inline_arrangement() -> None:
    state = _tube_bank_state(arrangement="inline")
    result = evaluate("tube_banks.grimison", state)
    assert result.metadata["arrangement"] == "inline"


def test_grimison_staggered_arrangement() -> None:
    state = _tube_bank_state(arrangement="staggered")
    result = evaluate("tube_banks.grimison", state)
    assert result.metadata["arrangement"] == "staggered"


# ---------------------------------------------------------------------------
# Žukauskas — Re regime boundaries
# ---------------------------------------------------------------------------


def _re_for_velocity(velocity: float, diameter: float = 0.02) -> float:
    # Re = rho * v * D / mu = 1.2 * v * D / 1.8e-5
    return 1.2 * velocity * diameter / 1.8e-5


def test_zukauskas_inline_re_lt_100() -> None:
    # Incropera Table 7.5: aligned Re 10-100 → C1=0.80, m=0.40
    state = _tube_bank_state(velocity=0.05, arrangement="inline")
    result = evaluate("tube_banks.zukauskas", state)
    assert result.metadata["arrangement"] == "inline"
    assert result.metadata["C"] == pytest.approx(0.80)
    assert result.metadata["m"] == pytest.approx(0.4)


def test_zukauskas_inline_re_100_to_1000_raises() -> None:
    # Incropera Table 7.5: for Re 100-1000, approximate as single isolated cylinder
    state = _tube_bank_state(velocity=0.375, arrangement="inline")
    with pytest.raises(ValueError, match="single isolated cylinder"):
        evaluate("tube_banks.zukauskas", state)


def test_zukauskas_inline_re_1000_to_2e5() -> None:
    state = _tube_bank_state(velocity=5.0, arrangement="inline")
    result = evaluate("tube_banks.zukauskas", state)
    re = result.metadata["re"]
    assert 1000 <= re < 2e5
    assert result.metadata["C"] == pytest.approx(0.27)
    assert result.metadata["m"] == pytest.approx(0.63)


def test_zukauskas_inline_re_ge_2e5() -> None:
    # Incropera Table 7.5: aligned Re 2e5-2e6 → C1=0.021, m=0.84
    state = _tube_bank_state(velocity=160.0, arrangement="inline")
    result = evaluate("tube_banks.zukauskas", state)
    re = result.metadata["re"]
    assert re >= 2e5
    assert result.metadata["C"] == pytest.approx(0.021)
    assert result.metadata["m"] == pytest.approx(0.84)


def test_zukauskas_staggered_re_lt_100() -> None:
    # Incropera Table 7.5: staggered Re 10-100 → C1=0.90, m=0.40
    state = _tube_bank_state(velocity=0.05, arrangement="staggered")
    result = evaluate("tube_banks.zukauskas", state)
    assert result.metadata["C"] == pytest.approx(0.90)
    assert result.metadata["m"] == pytest.approx(0.4)


def test_zukauskas_staggered_re_100_to_1000_raises() -> None:
    # Incropera Table 7.5: for Re 100-1000, approximate as single isolated cylinder
    state = _tube_bank_state(velocity=0.375, arrangement="staggered")
    with pytest.raises(ValueError, match="single isolated cylinder"):
        evaluate("tube_banks.zukauskas", state)


def test_zukauskas_staggered_re_1000_to_2e5_low_pitch_ratio() -> None:
    # S_T/S_L = 0.03/0.04 = 0.75 < 2 → C = 0.35 * 0.75^0.2
    state = _tube_bank_state(
        velocity=5.0,
        pitch_transverse=0.03,
        pitch_longitudinal=0.04,
        arrangement="staggered",
    )
    result = evaluate("tube_banks.zukauskas", state)
    re = result.metadata["re"]
    assert 1000 <= re < 2e5
    st_sl = 0.03 / 0.04
    expected_c = 0.35 * st_sl**0.2
    assert result.metadata["C"] == pytest.approx(expected_c)
    assert result.metadata["m"] == pytest.approx(0.6)


def test_zukauskas_staggered_re_1000_to_2e5_high_pitch_ratio() -> None:
    # S_T/S_L = 0.06/0.025 = 2.4 >= 2 → C1=0.40, m=0.60 (Incropera Table 7.5)
    state = _tube_bank_state(
        velocity=5.0,
        pitch_transverse=0.06,
        pitch_longitudinal=0.025,
        arrangement="staggered",
    )
    result = evaluate("tube_banks.zukauskas", state)
    re = result.metadata["re"]
    assert 1000 <= re < 2e5
    assert result.metadata["C"] == pytest.approx(0.40)
    assert result.metadata["m"] == pytest.approx(0.6)


def test_zukauskas_staggered_re_ge_2e5() -> None:
    # Incropera Table 7.5: staggered Re 2e5-2e6 → C1=0.022, m=0.84
    state = _tube_bank_state(velocity=160.0, arrangement="staggered")
    result = evaluate("tube_banks.zukauskas", state)
    re = result.metadata["re"]
    assert re >= 2e5
    assert result.metadata["C"] == pytest.approx(0.022)
    assert result.metadata["m"] == pytest.approx(0.84)


# ---------------------------------------------------------------------------
# Žukauskas — wall Prandtl correction
# ---------------------------------------------------------------------------


def test_zukauskas_wall_prandtl_applied_when_wall_viscosity_set() -> None:
    state = _tube_bank_state(wall_viscosity=1.2e-5)
    result = evaluate("tube_banks.zukauskas", state)
    assert result.metadata["wall_prandtl_applied"] is True


def test_zukauskas_wall_prandtl_not_applied_when_wall_viscosity_none() -> None:
    state = _tube_bank_state()
    result = evaluate("tube_banks.zukauskas", state)
    assert result.metadata["wall_prandtl_applied"] is False


def test_zukauskas_wall_correction_changes_nu() -> None:
    state_no_wall = _tube_bank_state()
    state_with_wall = _tube_bank_state(wall_viscosity=1.2e-5)
    nu_no_wall = evaluate("tube_banks.zukauskas", state_no_wall).value
    nu_with_wall = evaluate("tube_banks.zukauskas", state_with_wall).value
    # Values should differ when wall viscosity is present
    assert nu_no_wall != pytest.approx(nu_with_wall)


# ---------------------------------------------------------------------------
# Žukauskas — row correction metadata
# ---------------------------------------------------------------------------


def test_zukauskas_row_correction_not_applied() -> None:
    state = _tube_bank_state()
    result = evaluate("tube_banks.zukauskas", state)
    assert result.metadata["row_correction_applied"] is False


# ---------------------------------------------------------------------------
# Žukauskas — Nu output sanity
# ---------------------------------------------------------------------------


def test_zukauskas_nu_positive() -> None:
    state = _tube_bank_state()
    result = evaluate("tube_banks.zukauskas", state)
    assert result.value > 0


def test_zukauskas_nu_increases_with_re() -> None:
    state_lo = _tube_bank_state(velocity=2.0)
    state_hi = _tube_bank_state(velocity=10.0)
    nu_lo = evaluate("tube_banks.zukauskas", state_lo).value
    nu_hi = evaluate("tube_banks.zukauskas", state_hi).value
    assert nu_hi > nu_lo


# ---------------------------------------------------------------------------
# Žukauskas — manual calculation check
# ---------------------------------------------------------------------------


def test_zukauskas_inline_manual() -> None:
    # Re ~ 6667, Pr ~ 0.696, C=0.27, m=0.63, no wall correction
    # Nu = 0.27 * 6667^0.63 * 0.696^0.36
    state = _tube_bank_state(velocity=5.0, arrangement="inline")
    result = evaluate("tube_banks.zukauskas", state)
    re = 1.2 * 5.0 * 0.02 / 1.8e-5
    pr = 1005.0 * 1.8e-5 / 0.026
    expected = 0.27 * re**0.63 * pr**0.36
    assert result.value == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# Grimison — Nu output sanity
# ---------------------------------------------------------------------------


def test_grimison_nu_positive() -> None:
    state = _tube_bank_state()
    result = evaluate("tube_banks.grimison", state)
    assert result.value > 0


def test_grimison_nu_increases_with_re() -> None:
    state_lo = _tube_bank_state(velocity=2.0)
    state_hi = _tube_bank_state(velocity=10.0)
    nu_lo = evaluate("tube_banks.grimison", state_lo).value
    nu_hi = evaluate("tube_banks.grimison", state_hi).value
    assert nu_hi > nu_lo


def test_grimison_inline_manual() -> None:
    # C1=0.27, m1=0.63
    state = _tube_bank_state(velocity=5.0, arrangement="inline")
    result = evaluate("tube_banks.grimison", state)
    re = 1.2 * 5.0 * 0.02 / 1.8e-5
    pr = 1005.0 * 1.8e-5 / 0.026
    expected = 0.27 * re**0.63 * pr**0.36
    assert result.value == pytest.approx(expected, rel=1e-6)


def test_grimison_staggered_manual() -> None:
    # S_T/S_L = 0.03/0.04 = 0.75; C1=0.35*0.75^0.2, m1=0.6
    state = _tube_bank_state(
        velocity=5.0,
        pitch_transverse=0.03,
        pitch_longitudinal=0.04,
        arrangement="staggered",
    )
    result = evaluate("tube_banks.grimison", state)
    re = 1.2 * 5.0 * 0.02 / 1.8e-5
    pr = 1005.0 * 1.8e-5 / 0.026
    st_sl = 0.03 / 0.04
    c1 = 0.35 * st_sl**0.2
    expected = c1 * re**0.6 * pr**0.36
    assert result.value == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# Grimison — metadata
# ---------------------------------------------------------------------------


def test_grimison_inline_coefficients() -> None:
    state = _tube_bank_state(arrangement="inline")
    result = evaluate("tube_banks.grimison", state)
    assert result.metadata["C1"] == pytest.approx(0.27)
    assert result.metadata["m1"] == pytest.approx(0.63)


def test_grimison_staggered_coefficients() -> None:
    state = _tube_bank_state(
        pitch_transverse=0.03,
        pitch_longitudinal=0.04,
        arrangement="staggered",
    )
    result = evaluate("tube_banks.grimison", state)
    st_sl = 0.03 / 0.04
    assert result.metadata["C1"] == pytest.approx(0.35 * st_sl**0.2)
    assert result.metadata["m1"] == pytest.approx(0.6)


def test_grimison_metadata_has_re_pr_geometry() -> None:
    state = _tube_bank_state()
    result = evaluate("tube_banks.grimison", state)
    assert "re" in result.metadata
    assert "pr" in result.metadata
    assert result.metadata["geometry_type"] == "tube_bank"


# ---------------------------------------------------------------------------
# error cases — missing pitch fields
# ---------------------------------------------------------------------------


def test_zukauskas_raises_if_pitch_not_set() -> None:
    """State without tube_bank geometry has no pitch ratios."""
    state = EngineeringState(
        fluid=FluidProperties(
            density=1.2,
            viscosity=1.8e-5,
            thermal_conductivity=0.026,
            heat_capacity=1005.0,
        ),
        geometry=Geometry(
            geometry_type="cylinder_crossflow",
            characteristic_length=0.02,
        ),
        boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
        flow=FlowState(velocity=5.0),
    )
    with pytest.raises(ValueError, match="pitch"):
        evaluate("tube_banks.zukauskas", state)


def test_grimison_raises_if_pitch_not_set() -> None:
    state = EngineeringState(
        fluid=FluidProperties(
            density=1.2,
            viscosity=1.8e-5,
            thermal_conductivity=0.026,
            heat_capacity=1005.0,
        ),
        geometry=Geometry(
            geometry_type="cylinder_crossflow",
            characteristic_length=0.02,
        ),
        boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
        flow=FlowState(velocity=5.0),
    )
    with pytest.raises(ValueError, match="pitch"):
        evaluate("tube_banks.grimison", state)


# ---------------------------------------------------------------------------
# output_name
# ---------------------------------------------------------------------------


def test_zukauskas_output_name() -> None:
    state = _tube_bank_state()
    result = evaluate("tube_banks.zukauskas", state)
    assert result.output_name == "Nu"


def test_grimison_output_name() -> None:
    state = _tube_bank_state()
    result = evaluate("tube_banks.grimison", state)
    assert result.output_name == "Nu"
