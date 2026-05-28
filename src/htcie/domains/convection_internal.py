"""Internal forced convection domain helpers."""

from __future__ import annotations

from math import log

from htcie.core.results import EvaluationResult
from htcie.core.state import EngineeringState
from htcie.domains._helpers import require_re_pr

_DISPATCH: dict[str, object] = {}


def evaluate(key: str, state: EngineeringState) -> EvaluationResult:
    """Dispatch to the named internal-convection correlation."""
    fn = _DISPATCH.get(key)
    if fn is None:
        raise NotImplementedError(f"No evaluator implemented for {key}")
    return fn(state)  # type: ignore[operator]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _petukhov_friction_factor(re: float) -> float:
    r"""Petukhov (1970) smooth-tube friction factor.

    :math:`f = (0.790 \ln Re - 1.64)^{-2}`

    Valid for :math:`10^4 \leq Re \leq 5 \times 10^6`.
    """
    return (0.790 * log(re) - 1.64) ** -2


_require_re_pr = require_re_pr


# ---------------------------------------------------------------------------
# 1. Dittus-Boelter
# ---------------------------------------------------------------------------


def _dittus_boelter(state: EngineeringState) -> EvaluationResult:
    r"""Dittus-Boelter (1930): :math:`Nu = 0.023 \, Re^{0.8} \, Pr^n`.

    The exponent :math:`n = 0.4` for heating (:math:`T_w > T_b`) and
    :math:`n = 0.3` for cooling (:math:`T_w < T_b`). Defaults to :math:`n = 0.4`
    when wall or bulk temperatures are not provided.
    """
    re, pr = _require_re_pr(state)
    t_bulk = state.boundary.bulk_temperature
    t_wall = state.boundary.wall_temperature

    if t_bulk is not None and t_wall is not None and t_bulk > t_wall:
        n = 0.3
    else:
        n = 0.4

    nu = 0.023 * re**0.8 * pr**n
    return EvaluationResult(
        key="internal.dittus_boelter",
        output_name="Nu",
        value=float(nu),
        metadata={
            "re": re,
            "pr": pr,
            "n_exponent": n,
            "geometry_type": state.geometry.geometry_type,
        },
    )


_DISPATCH["internal.dittus_boelter"] = _dittus_boelter


# ---------------------------------------------------------------------------
# 2. Sieder-Tate
# ---------------------------------------------------------------------------


def _sieder_tate(state: EngineeringState) -> EvaluationResult:
    r"""Sieder-Tate (1936):
    :math:`Nu = 0.027 \, Re^{0.8} \, Pr^{1/3} \, (\mu/\mu_w)^{0.14}`.

    The viscosity-ratio correction :math:`(\mu/\mu_w)^{0.14}` is omitted
    (set to 1) when ``fluid.wall_viscosity`` is not provided.
    """
    re, pr = _require_re_pr(state)
    mu = state.fluid.viscosity
    mu_w = state.fluid.wall_viscosity

    if mu_w is None:
        viscosity_factor = 1.0
        viscosity_ratio_applied = False
    else:
        viscosity_factor = (mu / mu_w) ** 0.14
        viscosity_ratio_applied = True

    nu = 0.027 * re**0.8 * pr ** (1 / 3) * viscosity_factor
    return EvaluationResult(
        key="internal.sieder_tate",
        output_name="Nu",
        value=float(nu),
        metadata={
            "re": re,
            "pr": pr,
            "viscosity_ratio_applied": viscosity_ratio_applied,
            "geometry_type": state.geometry.geometry_type,
        },
    )


_DISPATCH["internal.sieder_tate"] = _sieder_tate


# ---------------------------------------------------------------------------
# 3. Gnielinski
# ---------------------------------------------------------------------------


def _gnielinski(state: EngineeringState) -> EvaluationResult:
    r"""Gnielinski (1976):
    :math:`Nu = \dfrac{(f/8)(Re - 1000)\,Pr}{1 + 12.7\sqrt{f/8}\,(Pr^{2/3} - 1)}`.

    The friction factor :math:`f` is computed from the Petukhov (1970) formula.
    Valid for :math:`3000 \leq Re \leq 5 \times 10^6` and :math:`0.5 \leq Pr \leq 2000`.
    Preferred over Dittus-Boelter for its lower stated uncertainty (~10 %).
    """
    re, pr = _require_re_pr(state)
    if re < 3000:
        raise ValueError(f"Gnielinski correlation requires Re >= 3000, got Re={re:.1f}")
    f = _petukhov_friction_factor(re)
    nu = (f / 8) * (re - 1000) * pr / (1 + 12.7 * (f / 8) ** 0.5 * (pr ** (2 / 3) - 1))
    return EvaluationResult(
        key="internal.gnielinski",
        output_name="Nu",
        value=float(nu),
        metadata={
            "re": re,
            "pr": pr,
            "friction_factor": f,
            "geometry_type": state.geometry.geometry_type,
        },
    )


_DISPATCH["internal.gnielinski"] = _gnielinski


# ---------------------------------------------------------------------------
# 4. Petukhov
# ---------------------------------------------------------------------------


def _petukhov(state: EngineeringState) -> EvaluationResult:
    r"""Petukhov (1970):
    :math:`Nu = \dfrac{(f/8)\,Re\,Pr}{1.07 + 12.7\sqrt{f/8}\,(Pr^{2/3} - 1)}`.

    Uses the Petukhov friction factor for smooth tubes. Valid for
    :math:`10^4 \leq Re \leq 5 \times 10^6` and :math:`0.5 \leq Pr \leq 2000`.
    """
    re, pr = _require_re_pr(state)
    f = _petukhov_friction_factor(re)
    nu = (f / 8) * re * pr / (1.07 + 12.7 * (f / 8) ** 0.5 * (pr ** (2 / 3) - 1))
    return EvaluationResult(
        key="internal.petukhov",
        output_name="Nu",
        value=float(nu),
        metadata={
            "re": re,
            "pr": pr,
            "friction_factor": f,
            "geometry_type": state.geometry.geometry_type,
        },
    )


_DISPATCH["internal.petukhov"] = _petukhov


# ---------------------------------------------------------------------------
# 5. Shah laminar
# ---------------------------------------------------------------------------


def _shah_laminar(state: EngineeringState) -> EvaluationResult:
    r"""Shah (1978) combined entry-length correlation for laminar flow.

    :math:`Nu = 3.66 + \dfrac{0.0668\,Gz}{1 + 0.04\,Gz^{2/3}}`

    where the Graetz number :math:`Gz = Re \cdot Pr \cdot (D_h / L)`.
    Falls back to :math:`Nu = 3.66` (fully developed UWT) when
    ``developing_length`` is not provided.
    """
    re, pr = _require_re_pr(state)
    D = state.geometry.hydraulic_diameter or state.geometry.characteristic_length
    L = state.flow.developing_length

    if L is None:
        nu = 3.66
        gz: float | None = None
    else:
        gz = re * pr * (D / L)
        nu = 3.66 + (0.0668 * gz) / (1 + 0.04 * gz ** (2 / 3))

    return EvaluationResult(
        key="internal.shah_laminar",
        output_name="Nu",
        value=float(nu),
        metadata={
            "re": re,
            "pr": pr,
            "graetz": gz,
            "geometry_type": state.geometry.geometry_type,
        },
    )


_DISPATCH["internal.shah_laminar"] = _shah_laminar


# ---------------------------------------------------------------------------
# 6. Churchill-Ozoe
# ---------------------------------------------------------------------------


def _churchill_ozoe(state: EngineeringState) -> EvaluationResult:
    r"""Churchill-Ozoe (1973): laminar base + thermally-developing Hausen correction.

    :math:`Nu = Nu_0 + \dfrac{0.0668\,Gz}{1 + 0.04\,Gz^{2/3}}`

    where :math:`Nu_0 = 3.66` for constant wall temperature (UWT) and
    :math:`Nu_0 = 4.36` for constant heat flux (UHF). Falls back to
    :math:`Nu_0` alone when ``developing_length`` is not provided.
    """
    re, pr = _require_re_pr(state)
    bt = state.boundary.boundary_type
    D = state.geometry.hydraulic_diameter or state.geometry.characteristic_length
    L = state.flow.developing_length
    gz: float | None = re * pr * (D / L) if L is not None else None

    nu_base = 3.66 if bt == "constant_wall_temperature" else 4.36

    if gz is not None:
        nu = nu_base + (0.0668 * gz) / (1 + 0.04 * gz ** (2 / 3))
    else:
        nu = nu_base

    return EvaluationResult(
        key="internal.churchill_ozoe",
        output_name="Nu",
        value=float(nu),
        metadata={
            "re": re,
            "pr": pr,
            "graetz": gz,
            "boundary_type": bt,
            "geometry_type": state.geometry.geometry_type,
        },
    )


_DISPATCH["internal.churchill_ozoe"] = _churchill_ozoe
