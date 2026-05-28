"""Canonical engineering state models and derived dimensionless groups."""

from __future__ import annotations

import math
from typing import Literal, Optional

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator


class FluidProperties(BaseModel):
    """Thermophysical properties of the working fluid at bulk conditions.

    All properties are assumed constant (evaluated at bulk temperature) unless
    wall_viscosity is provided, in which case the viscosity-ratio correction
    can be applied by eligible correlations (Sieder-Tate, Žukauskas).
    """

    density: float = Field(..., gt=0, description="Fluid density [kg/m^3]")
    viscosity: float = Field(..., gt=0, description="Dynamic viscosity [Pa·s]")
    thermal_conductivity: float = Field(
        ..., gt=0, description="Thermal conductivity [W/m·K]"
    )
    heat_capacity: float = Field(
        ..., gt=0, description="Specific heat capacity [J/kg·K]"
    )
    wall_viscosity: float | None = Field(
        None,
        gt=0,
        description="Dynamic viscosity at wall temperature [Pa·s], required for"
        " Sieder-Tate viscosity correction",
    )

    @field_validator("density", "viscosity", "thermal_conductivity", "heat_capacity")
    @classmethod
    def _must_be_finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("must be a finite number")
        return v

    @field_validator("wall_viscosity")
    @classmethod
    def _wall_viscosity_finite(cls, v: float | None) -> float | None:
        if v is not None and not math.isfinite(v):
            raise ValueError("must be a finite number")
        return v


class Geometry(BaseModel):
    """Geometric description of the heat-transfer surface.

    The characteristic_length drives the Reynolds number when hydraulic_diameter
    is not provided. For circular tubes, set both characteristic_length and
    hydraulic_diameter to the inner diameter D. For tube banks, pitch fields
    are required to determine the inline/staggered arrangement.
    """

    geometry_type: Literal[
        "circular_tube", "cylinder_crossflow", "flat_plate", "tube_bank"
    ]
    characteristic_length: float = Field(
        ..., gt=0, description="Characteristic length [m]"
    )
    hydraulic_diameter: Optional[float] = Field(
        None, gt=0, description="Hydraulic diameter [m]"
    )
    roughness: float = Field(0.0, ge=0, description="Surface roughness [m]")
    pitch_transverse: Optional[float] = Field(None, gt=0)
    pitch_longitudinal: Optional[float] = Field(None, gt=0)
    arrangement: Optional[Literal["inline", "staggered"]] = Field(
        None,
        description="Tube bank arrangement; required when geometry_type='tube_bank'",
    )

    @field_validator("characteristic_length")
    @classmethod
    def _char_len_finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("must be a finite number")
        return v

    @field_validator(
        "hydraulic_diameter", "roughness", "pitch_transverse", "pitch_longitudinal"
    )
    @classmethod
    def _optional_floats_finite(cls, v: float | None) -> float | None:
        if v is not None and not math.isfinite(v):
            raise ValueError("must be a finite number")
        return v


class BoundaryConditions(BaseModel):
    """Thermal boundary conditions at the heat-transfer surface.

    The boundary_type distinguishes between isothermal (UWT) and isoflux (UHF)
    conditions, which affects the fully-developed Nusselt number for laminar
    flow (3.66 vs 4.36) and the exponent n in Dittus-Boelter (0.3 vs 0.4).
    Providing wall_temperature and bulk_temperature allows the Dittus-Boelter
    exponent to be selected automatically based on heating or cooling.
    """

    boundary_type: Literal["constant_wall_temperature", "constant_heat_flux"]
    wall_temperature: Optional[float] = Field(None, description="Wall temperature [K]")
    bulk_temperature: Optional[float] = Field(None, description="Bulk temperature [K]")

    @field_validator("wall_temperature", "bulk_temperature")
    @classmethod
    def _temps_finite(cls, v: float | None) -> float | None:
        if v is not None and not math.isfinite(v):
            raise ValueError("must be a finite number")
        return v


class FlowState(BaseModel):
    """Flow conditions at the inlet or representative cross-section.

    velocity is the bulk mean (average) velocity used to compute Re. For
    tube-bank problems it represents the maximum velocity in the narrowest
    cross-section. developing_length enables Graetz-number and entry-length
    corrections in laminar correlations (Shah, Churchill-Ozoe).
    """

    velocity: float = Field(..., gt=0, description="Characteristic velocity [m/s]")
    mass_flow_rate: Optional[float] = Field(
        None, gt=0, description="Mass flow rate [kg/s]"
    )
    developing_length: Optional[float] = Field(
        None, gt=0, description="Developing-flow axial position [m]"
    )

    @field_validator("velocity")
    @classmethod
    def _velocity_finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("must be a finite number")
        return v

    @field_validator("mass_flow_rate", "developing_length")
    @classmethod
    def _optional_flow_finite(cls, v: float | None) -> float | None:
        if v is not None and not math.isfinite(v):
            raise ValueError("must be a finite number")
        return v


class EngineeringState(BaseModel):
    """Canonical engineering state for a single-phase forced-convection problem.

    This is the single object passed through every layer of the pipeline. It
    combines fluid properties, geometry, boundary conditions, and flow state,
    and exposes all derived dimensionless groups as computed fields so that
    domain evaluators never recompute them independently.

    Computed fields (read-only):

    - **reynolds**: :math:`Re = \\rho V L / \\mu`
      (:math:`L` = ``hydraulic_diameter`` if set, else ``characteristic_length``)
    - **prandtl**: :math:`Pr = c_p \\mu / k`
    - **relative_roughness**: :math:`\\varepsilon / D_h`, or ``None`` if
      ``hydraulic_diameter`` is absent
    - **graetz**: :math:`Gz = Re \\cdot Pr \\cdot (D_h / L)`, or ``None`` if
      ``developing_length`` is absent
    - **entry_length_ratio**: :math:`x/D = L_{dev} / D_h`, or ``None``
    - **pitch_ratio_transverse**: :math:`S_T / D`, or ``None`` for non-tube-bank
      geometries
    - **pitch_ratio_longitudinal**: :math:`S_L / D`, or ``None`` for non-tube-bank
      geometries
    """

    fluid: FluidProperties
    geometry: Geometry
    boundary: BoundaryConditions
    flow: FlowState

    @model_validator(mode="after")
    def validate_tube_bank_fields(self) -> "EngineeringState":
        if self.geometry.geometry_type == "tube_bank":
            if (
                self.geometry.pitch_transverse is None
                or self.geometry.pitch_longitudinal is None
            ):
                raise ValueError(
                    "tube_bank geometry requires transverse and longitudinal pitch"
                )
            if self.geometry.arrangement is None:
                raise ValueError(
                    "tube_bank geometry requires arrangement ('inline' or 'staggered')"
                )
        return self

    @computed_field(return_type=float)  # type: ignore[prop-decorator]
    @property
    def reynolds(self) -> float:
        r"""Reynolds number :math:`Re = \rho V L / \mu`.

        Uses ``hydraulic_diameter`` as the length scale when set, falling back
        to ``characteristic_length``. This matches the convention used by all
        internal and external convection correlations in the registry.
        """
        L = self.geometry.hydraulic_diameter or self.geometry.characteristic_length
        return self.fluid.density * self.flow.velocity * L / self.fluid.viscosity

    @computed_field(return_type=float)  # type: ignore[prop-decorator]
    @property
    def prandtl(self) -> float:
        r"""Prandtl number :math:`Pr = c_p \mu / k`."""
        return (
            self.fluid.heat_capacity
            * self.fluid.viscosity
            / self.fluid.thermal_conductivity
        )

    @computed_field(return_type=float | None)  # type: ignore[prop-decorator]
    @property
    def relative_roughness(self) -> float | None:
        r"""Relative roughness :math:`\varepsilon / D_h`
        = ``roughness`` / ``hydraulic_diameter``.

        Returns ``None`` when ``hydraulic_diameter`` is not specified. Used by
        the Petukhov friction-factor formula (smooth tube assumed when absent).
        """
        D = self.geometry.hydraulic_diameter
        if D:
            return self.geometry.roughness / D
        return None

    @computed_field(return_type=float | None)  # type: ignore[prop-decorator]
    @property
    def graetz(self) -> float | None:
        r"""Graetz number :math:`Gz = Re \cdot Pr \cdot (D_h / L)`
        for thermally developing flow."""
        D_h = self.geometry.hydraulic_diameter
        L = self.flow.developing_length
        if D_h is None or L is None:
            return None
        return self.reynolds * self.prandtl * (D_h / L)

    @computed_field(return_type=float | None)  # type: ignore[prop-decorator]
    @property
    def entry_length_ratio(self) -> float | None:
        r"""Dimensionless entry length :math:`x/D = L_{dev} / D_h`."""
        D_h = self.geometry.hydraulic_diameter
        L = self.flow.developing_length
        if D_h is None or L is None:
            return None
        return L / D_h

    @computed_field(return_type=float | None)  # type: ignore[prop-decorator]
    @property
    def pitch_ratio_transverse(self) -> float | None:
        r"""Transverse pitch ratio :math:`S_T / D`
        = ``pitch_transverse`` / ``characteristic_length``."""
        S_T = self.geometry.pitch_transverse
        D = self.geometry.characteristic_length
        if S_T is None or D == 0:
            return None
        return S_T / D

    @computed_field(return_type=float | None)  # type: ignore[prop-decorator]
    @property
    def pitch_ratio_longitudinal(self) -> float | None:
        r"""Longitudinal pitch ratio :math:`S_L / D`
        = ``pitch_longitudinal`` / ``characteristic_length``."""
        S_L = self.geometry.pitch_longitudinal
        D = self.geometry.characteristic_length
        if S_L is None or D == 0:
            return None
        return S_L / D
