from htcie.core.state import (
    BoundaryConditions,
    EngineeringState,
    FlowState,
    FluidProperties,
    Geometry,
)


def _water_in_tube(
    *,
    hydraulic_diameter: float = 0.01,
    developing_length: float | None = None,
    pitch_transverse: float | None = None,
    pitch_longitudinal: float | None = None,
    geometry_type: str = "circular_tube",
    wall_viscosity: float | None = None,
) -> EngineeringState:
    """Helper: water at ~20 °C flowing in a tube at 1 m/s."""
    return EngineeringState(
        fluid=FluidProperties(
            density=997.0,
            viscosity=0.00089,
            thermal_conductivity=0.6,
            heat_capacity=4180.0,
            wall_viscosity=wall_viscosity,
        ),
        geometry=Geometry(
            geometry_type=geometry_type,  # type: ignore[arg-type]
            characteristic_length=hydraulic_diameter,
            hydraulic_diameter=hydraulic_diameter,
            pitch_transverse=pitch_transverse,
            pitch_longitudinal=pitch_longitudinal,
        ),
        boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
        flow=FlowState(velocity=1.0, developing_length=developing_length),
    )


def test_reynolds_and_prandtl_are_computed() -> None:
    state = EngineeringState(
        fluid=FluidProperties(
            density=997.0,
            viscosity=0.00089,
            thermal_conductivity=0.6,
            heat_capacity=4180.0,
        ),
        geometry=Geometry(
            geometry_type="circular_tube",
            characteristic_length=0.01,
            hydraulic_diameter=0.01,
        ),
        boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
        flow=FlowState(velocity=1.0),
    )
    assert state.reynolds > 0
    assert state.prandtl > 0


def test_wall_viscosity_accepted_on_fluid_properties() -> None:
    state = _water_in_tube(wall_viscosity=0.00065)
    assert state.fluid.wall_viscosity == 0.00065


def test_wall_viscosity_defaults_to_none() -> None:
    state = _water_in_tube()
    assert state.fluid.wall_viscosity is None


def test_graetz_computed_correctly() -> None:
    # Water in a 10 mm tube, axial position L = 0.1 m
    # Re = rho * v * D / mu = 997 * 1.0 * 0.01 / 0.00089 ≈ 11202.25
    # Pr = cp * mu / k = 4180 * 0.00089 / 0.6 ≈ 6.1967
    # Gz = Re * Pr * (D / L) = Re * Pr * (0.01 / 0.1) = Re * Pr * 0.1
    state = _water_in_tube(hydraulic_diameter=0.01, developing_length=0.1)
    expected = state.reynolds * state.prandtl * (0.01 / 0.1)
    assert state.graetz is not None
    assert abs(state.graetz - expected) < 1e-9


def test_graetz_is_none_when_developing_length_not_set() -> None:
    state = _water_in_tube(hydraulic_diameter=0.01)
    assert state.graetz is None


def test_graetz_is_none_when_hydraulic_diameter_not_set() -> None:
    state = EngineeringState(
        fluid=FluidProperties(
            density=997.0,
            viscosity=0.00089,
            thermal_conductivity=0.6,
            heat_capacity=4180.0,
        ),
        geometry=Geometry(
            geometry_type="circular_tube",
            characteristic_length=0.01,
            hydraulic_diameter=None,
        ),
        boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
        flow=FlowState(velocity=1.0, developing_length=0.1),
    )
    assert state.graetz is None


def test_entry_length_ratio_computed_correctly() -> None:
    # x/D = 0.5 / 0.01 = 50
    state = _water_in_tube(hydraulic_diameter=0.01, developing_length=0.5)
    assert state.entry_length_ratio is not None
    assert abs(state.entry_length_ratio - 50.0) < 1e-9


def test_entry_length_ratio_is_none_when_developing_length_not_set() -> None:
    state = _water_in_tube(hydraulic_diameter=0.01)
    assert state.entry_length_ratio is None


def test_pitch_ratios_computed_for_tube_bank() -> None:
    # characteristic_length = D = 0.02 m, S_T = 0.04 m, S_L = 0.03 m
    # pitch_ratio_transverse = 0.04 / 0.02 = 2.0
    # pitch_ratio_longitudinal = 0.03 / 0.02 = 1.5
    state = EngineeringState(
        fluid=FluidProperties(
            density=997.0,
            viscosity=0.00089,
            thermal_conductivity=0.6,
            heat_capacity=4180.0,
        ),
        geometry=Geometry(
            geometry_type="tube_bank",
            characteristic_length=0.02,
            pitch_transverse=0.04,
            pitch_longitudinal=0.03,
            arrangement="inline",
        ),
        boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
        flow=FlowState(velocity=1.0),
    )
    assert state.pitch_ratio_transverse is not None
    assert abs(state.pitch_ratio_transverse - 2.0) < 1e-9
    assert state.pitch_ratio_longitudinal is not None
    assert abs(state.pitch_ratio_longitudinal - 1.5) < 1e-9


def test_pitch_ratio_transverse_is_none_when_not_set() -> None:
    state = _water_in_tube()
    assert state.pitch_ratio_transverse is None


def test_pitch_ratio_longitudinal_is_none_when_not_set() -> None:
    state = _water_in_tube()
    assert state.pitch_ratio_longitudinal is None
