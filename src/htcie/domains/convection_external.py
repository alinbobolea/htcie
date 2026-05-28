"""External forced convection domain — cylinders and flat plates."""

from __future__ import annotations

from htcie.core.results import EvaluationResult
from htcie.core.state import EngineeringState
from htcie.domains._helpers import require_re_pr


def evaluate(key: str, state: EngineeringState) -> EvaluationResult:
    """Dispatch to the named external-convection correlation."""
    fn = _DISPATCH.get(key)
    if fn is None:
        raise NotImplementedError(f"No evaluator implemented for key: {key}")
    return fn(state)  # type: ignore[operator]


_require_re_pr = require_re_pr


# ---------------------------------------------------------------------------
# 1. Churchill-Bernstein
# ---------------------------------------------------------------------------


def _churchill_bernstein(state: EngineeringState) -> EvaluationResult:
    r"""Churchill-Bernstein (1977): :math:`Nu` for a cylinder in crossflow.

    .. math::

        Nu = 0.3 + \frac{0.62\,Re^{1/2}\,Pr^{1/3}}
             {\left[1 + (0.4/Pr)^{2/3}\right]^{1/4}}
             \left[1 + \left(\frac{Re}{282000}\right)^{5/8}\right]^{4/5}

    Preferred all-:math:`Re` correlation for cylinders in crossflow. Valid for
    :math:`Re \cdot Pr \geq 0.2`. Per the original paper this formula is a
    lower bound — experimental values typically lie above it.
    """
    re, pr = _require_re_pr(state)
    nu = 0.3 + (
        (0.62 * re**0.5 * pr ** (1 / 3))
        / (1 + (0.4 / pr) ** (2 / 3)) ** 0.25
        * (1 + (re / 282000) ** (5 / 8)) ** (4 / 5)
    )
    return EvaluationResult(
        key="external.churchill_bernstein",
        output_name="Nu",
        value=float(nu),
        metadata={
            "re": re,
            "pr": pr,
            "geometry_type": state.geometry.geometry_type,
        },
    )


# ---------------------------------------------------------------------------
# 2. Hilpert
# ---------------------------------------------------------------------------

_HILPERT_TABLE: list[tuple[float, float, float, float]] = [
    (0.4, 4.0, 0.989, 0.330),
    (4.0, 40.0, 0.911, 0.385),
    (40.0, 4000.0, 0.683, 0.466),
    (4000.0, 40000.0, 0.193, 0.618),
    (40000.0, 400000.0, 0.027, 0.805),
]


def _hilpert_coefficients(re: float) -> tuple[float, float]:
    r"""Return :math:`(C, m)` from the Hilpert (1933) table for the given :math:`Re`.

    Uses inclusive upper bounds (``re_lo <= re <= re_hi``) so the table maximum
    Re=400,000 is covered by the last band.
    """
    for re_lo, re_hi, c, m in _HILPERT_TABLE:
        if re_lo <= re <= re_hi:
            return c, m
    raise ValueError(
        f"Re={re} is outside the Hilpert correlation validity range [0.4, 400000]"
    )


def _hilpert(state: EngineeringState) -> EvaluationResult:
    r"""Hilpert (1933): :math:`Nu = C \, Re^m \, Pr^{1/3}`.

    Coefficients :math:`C` and :math:`m` are selected from a table keyed on
    :math:`Re` band. Valid for :math:`0.4 \leq Re \leq 400{,}000`.
    """
    re, pr = _require_re_pr(state)
    c, m = _hilpert_coefficients(re)
    nu = c * re**m * pr ** (1 / 3)
    return EvaluationResult(
        key="external.hilpert",
        output_name="Nu",
        value=float(nu),
        metadata={
            "re": re,
            "pr": pr,
            "hilpert_C": c,
            "hilpert_m": m,
            "geometry_type": state.geometry.geometry_type,
        },
    )


# ---------------------------------------------------------------------------
# 3. Žukauskas cylinder
# ---------------------------------------------------------------------------

_ZUKAUSKAS_TABLE: list[tuple[float, float, float, float]] = [
    (1.0, 40.0, 0.75, 0.4),
    (40.0, 1000.0, 0.51, 0.5),
    (1000.0, 200000.0, 0.26, 0.6),
    (200000.0, 1000000.0, 0.076, 0.7),
]


def _zukauskas_coefficients(re: float) -> tuple[float, float]:
    r"""Return :math:`(C, m)` from the Žukauskas (1972) table for the given :math:`Re`.

    Uses inclusive upper bounds (``re_lo <= re <= re_hi``) so the table maximum
    Re=1,000,000 is covered by the last band.
    """
    for re_lo, re_hi, c, m in _ZUKAUSKAS_TABLE:
        if re_lo <= re <= re_hi:
            return c, m
    raise ValueError(
        f"Re={re} is outside the Žukauskas correlation validity range [1, 1000000]"
    )


def _zukauskas_cylinder(state: EngineeringState) -> EvaluationResult:
    r"""Žukauskas (1972): :math:`Nu = C \, Re^m \, Pr^n \, (Pr/Pr_w)^{0.25}`.

    Per Incropera Table 7.4 / Eq 7.53: :math:`n = 0.37` for :math:`Pr \leq 10`,
    :math:`n = 0.36` for :math:`Pr > 10`. The wall-Prandtl correction
    :math:`(Pr/Pr_w)^{0.25}` is omitted (set to 1) when ``fluid.wall_viscosity``
    is not provided. Coefficients :math:`C` and :math:`m` are selected from a
    table keyed on :math:`Re` band.
    """
    re, pr = _require_re_pr(state)
    c, m = _zukauskas_coefficients(re)

    mu_w = state.fluid.wall_viscosity
    if mu_w is not None:
        pr_w = state.fluid.heat_capacity * mu_w / state.fluid.thermal_conductivity
        viscosity_correction = (pr / pr_w) ** 0.25
        wall_prandtl_applied = True
    else:
        viscosity_correction = 1.0
        wall_prandtl_applied = False

    n = 0.37 if pr <= 10.0 else 0.36
    nu = c * re**m * pr**n * viscosity_correction
    meta: dict[str, object] = {
        "re": re,
        "pr": pr,
        "zukauskas_C": c,
        "zukauskas_m": m,
        "pr_exponent_n": n,
        "wall_prandtl_applied": wall_prandtl_applied,
        "geometry_type": state.geometry.geometry_type,
    }
    if wall_prandtl_applied:
        meta["wall_prandtl_note"] = (
            "Pr_w approximated using bulk cp and k with wall viscosity mu_w"
        )
    return EvaluationResult(
        key="external.zukauskas_cylinder",
        output_name="Nu",
        value=float(nu),
        metadata=meta,
    )


# ---------------------------------------------------------------------------
# 4. Pohlhausen plate (laminar)
# ---------------------------------------------------------------------------


def _pohlhausen_plate(state: EngineeringState) -> EvaluationResult:
    r"""Pohlhausen (1921): :math:`Nu_L = 0.664 \, Re_L^{1/2} \, Pr^{1/3}`
    for a laminar flat plate.

    Valid for :math:`Re_L < 5 \times 10^5` and :math:`Pr \geq 0.6`.
    """
    re, pr = _require_re_pr(state)
    if re >= 5e5:
        raise ValueError(
            f"Pohlhausen correlation is valid for Re < 5e5 (laminar), got Re={re:.1f}"
        )
    if pr < 0.6:
        raise ValueError(f"Pohlhausen correlation requires Pr >= 0.6, got Pr={pr:.3f}")
    nu = 0.664 * re**0.5 * pr ** (1 / 3)
    return EvaluationResult(
        key="external.pohlhausen_plate",
        output_name="Nu",
        value=float(nu),
        metadata={
            "re": re,
            "pr": pr,
            "geometry_type": state.geometry.geometry_type,
        },
    )


# ---------------------------------------------------------------------------
# 5. Mixed boundary layer flat plate (turbulent)
# ---------------------------------------------------------------------------


def _turbulent_plate(state: EngineeringState) -> EvaluationResult:
    r"""Mixed boundary-layer flat plate:
    :math:`Nu_L = (0.037 \, Re_L^{0.8} - 871) \, Pr^{1/3}`.

    Accounts for the laminar leading-edge region assuming transition at
    :math:`Re_{x,c} = 5 \times 10^5`. Valid for :math:`Re_L \geq 5 \times 10^5`.
    """
    re, pr = _require_re_pr(state)
    if re < 5e5:
        raise ValueError(
            f"Turbulent plate correlation requires Re >= 5e5, got Re={re:.1f}"
        )
    nu = (0.037 * re**0.8 - 871) * pr ** (1 / 3)
    return EvaluationResult(
        key="external.turbulent_plate",
        output_name="Nu",
        value=float(nu),
        metadata={
            "re": re,
            "pr": pr,
            "geometry_type": state.geometry.geometry_type,
        },
    )


# ---------------------------------------------------------------------------
# dispatch table
# ---------------------------------------------------------------------------

_DISPATCH: dict[str, object] = {
    "external.churchill_bernstein": _churchill_bernstein,
    "external.hilpert": _hilpert,
    "external.zukauskas_cylinder": _zukauskas_cylinder,
    "external.pohlhausen_plate": _pohlhausen_plate,
    "external.turbulent_plate": _turbulent_plate,
}
