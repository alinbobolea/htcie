"""Tube-bank / bundle domain — Žukauskas and Grimison correlations."""

from __future__ import annotations

from htcie.core.results import EvaluationResult
from htcie.core.state import EngineeringState
from htcie.domains._helpers import require_re_pr


def evaluate(key: str, state: EngineeringState) -> EvaluationResult:
    """Dispatch to the named tube-bank correlation."""
    fn = _DISPATCH.get(key)
    if fn is None:
        raise NotImplementedError(f"No evaluator implemented for key: {key}")
    return fn(state)  # type: ignore[operator]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_require_re_pr = require_re_pr


def _pitch_ratio(state: EngineeringState) -> float:
    """Return S_T/S_L from pitch ratio fields.

    Requires both pitch_ratio_transverse and pitch_ratio_longitudinal to be set.
    """
    st_d = state.pitch_ratio_transverse
    sl_d = state.pitch_ratio_longitudinal
    if st_d is None or sl_d is None:
        raise ValueError(
            "tube_bank correlations require pitch_transverse and pitch_longitudinal"
        )
    if sl_d == 0:
        raise ValueError("pitch_ratio_longitudinal must be non-zero")
    return st_d / sl_d


def _require_arrangement(state: EngineeringState) -> str:
    """Return the tube bank arrangement from state geometry.

    Raises:
        ValueError: If ``geometry.arrangement`` is not set.
    """
    arrangement = state.geometry.arrangement
    if arrangement is None:
        raise ValueError(
            "tube_bank correlations require geometry.arrangement "
            "('inline' or 'staggered')"
        )
    return arrangement


# ---------------------------------------------------------------------------
# 1. Žukauskas tube bank
# ---------------------------------------------------------------------------


def _zukauskas_coefficients(
    re: float, arrangement: str, st_sl: float
) -> tuple[float, float]:
    r"""Return :math:`(C_1, m)` for the Žukauskas (1972) tube-bank correlation.

    Coefficients from Incropera 7th ed. Table 7.5. For
    :math:`100 \leq Re < 1000`, Incropera states to approximate as a single
    isolated cylinder; this range raises :exc:`ValueError` directing callers
    to use ``external.zukauskas_cylinder`` instead.

    For staggered arrangements at :math:`1000 \leq Re < 2 \times 10^5`:

    * :math:`S_T/S_L < 2`: :math:`C_1 = 0.35\,(S_T/S_L)^{0.2}`
    * :math:`S_T/S_L \geq 2`: :math:`C_1 = 0.40`
    """
    if arrangement == "inline":
        if re < 100:
            return 0.80, 0.40
        elif re < 1000:
            raise ValueError(
                "For 100 ≤ Re_D,max < 1000 Incropera Table 7.5 recommends "
                "approximating as a single isolated cylinder; "
                "use external.zukauskas_cylinder instead."
            )
        elif re < 2e5:
            return 0.27, 0.63
        else:
            return 0.021, 0.84
    else:  # staggered
        if re < 100:
            return 0.90, 0.40
        elif re < 1000:
            raise ValueError(
                "For 100 ≤ Re_D,max < 1000 Incropera Table 7.5 recommends "
                "approximating as a single isolated cylinder; "
                "use external.zukauskas_cylinder instead."
            )
        elif re < 2e5:
            if st_sl >= 2.0:
                return 0.40, 0.60
            return 0.35 * st_sl**0.2, 0.60
        else:
            return 0.022, 0.84


def _zukauskas(state: EngineeringState) -> EvaluationResult:
    r"""Žukauskas (1972) tube-bank correlation.

    :math:`Nu = C_1 Re_{D,max}^m Pr^{0.36} (Pr/Pr_w)^{0.25} F`

    The wall-Prandtl correction :math:`(Pr/Pr_w)^{0.25}` is omitted (set to 1)
    when ``fluid.wall_viscosity`` is not provided. The row correction factor
    :math:`F = 1.0` (full row-count correction tables require ``N_rows`` which
    is not present in the current state model).
    """
    re, pr = _require_re_pr(state)
    st_sl = _pitch_ratio(state)
    arrangement = _require_arrangement(state)
    c, m = _zukauskas_coefficients(re, arrangement, st_sl)

    st_d = state.pitch_ratio_transverse
    sl_d = state.pitch_ratio_longitudinal

    mu_w = state.fluid.wall_viscosity
    if mu_w is not None:
        pr_w = state.fluid.heat_capacity * mu_w / state.fluid.thermal_conductivity
        wall_correction = (pr / pr_w) ** 0.25
        wall_prandtl_applied = True
    else:
        wall_correction = 1.0
        wall_prandtl_applied = False

    # Row correction factor: 1.0 — requires N_rows not in current state model
    f_row = 1.0

    nu = c * re**m * pr**0.36 * wall_correction * f_row

    meta: dict[str, object] = {
        "re": re,
        "pr": pr,
        "arrangement": arrangement,
        "C": c,
        "m": m,
        "st_d": st_d,
        "sl_d": sl_d,
        "row_correction_applied": False,
        "wall_prandtl_applied": wall_prandtl_applied,
        "geometry_type": state.geometry.geometry_type,
    }
    if wall_prandtl_applied:
        meta["wall_prandtl_note"] = (
            "Pr_w approximated using bulk cp and k with wall viscosity mu_w"
        )
    return EvaluationResult(
        key="tube_banks.zukauskas",
        output_name="Nu",
        value=float(nu),
        metadata=meta,
    )


# ---------------------------------------------------------------------------
# 2. Grimison tube bank
# ---------------------------------------------------------------------------


def _grimison_coefficients(arrangement: str, st_sl: float) -> tuple[float, float]:
    r"""Return :math:`(C_1, m_1)` for the Grimison (1937) tube-bank correlation.

    Uses simplified constants from Incropera/DeWitt Table 7.1.
    Valid for :math:`1000 \leq Re \leq 2 \times 10^5`.
    """
    if arrangement == "inline":
        return 0.27, 0.63
    else:  # staggered
        return 0.35 * st_sl**0.2, 0.6


def _grimison(state: EngineeringState) -> EvaluationResult:
    r"""Grimison (1937): :math:`Nu = C_1 \, Re_D^{m_1} \, Pr^{0.36}` for tube banks.

    Uses simplified constants from Incropera/DeWitt Table 7.1. Valid for
    :math:`1000 \leq Re \leq 2 \times 10^5`. No wall-temperature correction
    applied; use Žukauskas when :math:`(Pr/Pr_w)^{0.25}` matters.
    """
    re, pr = _require_re_pr(state)
    st_sl = _pitch_ratio(state)
    arrangement = _require_arrangement(state)
    c1, m1 = _grimison_coefficients(arrangement, st_sl)

    st_d = state.pitch_ratio_transverse
    sl_d = state.pitch_ratio_longitudinal

    nu = c1 * re**m1 * pr**0.36

    return EvaluationResult(
        key="tube_banks.grimison",
        output_name="Nu",
        value=float(nu),
        metadata={
            "re": re,
            "pr": pr,
            "arrangement": arrangement,
            "C1": c1,
            "m1": m1,
            "st_d": st_d,
            "sl_d": sl_d,
            "geometry_type": state.geometry.geometry_type,
        },
    )


# ---------------------------------------------------------------------------
# dispatch table
# ---------------------------------------------------------------------------

_DISPATCH: dict[str, object] = {
    "tube_banks.zukauskas": _zukauskas,
    "tube_banks.grimison": _grimison,
}
