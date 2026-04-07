"""Deterministic ranking and scoring v1 for correlation candidates."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from htcie.core.registry import CorrelationMetadata
from htcie.core.state import EngineeringState

# Keys that implement viscosity-ratio correction (μ/μ_w)
_VISCOSITY_CORRECTION_KEYS = frozenset(
    {
        "internal.sieder_tate",
        "external.zukauskas_cylinder",
        "tube_banks.zukauskas",
    }
)

# Keys that handle thermally-developing / entry-length flow
_ENTRY_LENGTH_KEYS = frozenset(
    {
        "internal.shah_laminar",
        "internal.churchill_ozoe",
    }
)

# Re regime classification thresholds (Incropera §8.1, §7.2)
RE_LAMINAR_MAX: float = 2300.0  # Internal flow: fully laminar below this
RE_TRANSITION_MAX: float = 10_000.0  # Internal flow: fully turbulent above this
RE_PLATE_TURBULENT: float = 5e5  # Flat plate: turbulent transition


class ScoringWeightsV1(BaseModel):
    """Versioned scoring weights for htcie ranking v1.1.

    All factor weights sum to 1.0 (excluding extrapolation which is a
    penalty subtracted from the total).

    v1.1 changes vs v1:

    - ``uncertainty`` raised from 0.05 to 0.15 — primary source-quality signal.
    - ``pedigree`` lowered from 0.10 to 0.00 — redundant when uncertainty is
      properly weighted. The ``_pedigree()`` function is retained for potential
      future reactivation with a non-year-based signal.
    """

    version: str = "v1.1"
    validity: float = 0.30
    geometry: float = 0.20
    regime: float = 0.15
    boundary: float = 0.10
    corrections: float = 0.10
    pedigree: float = 0.00
    uncertainty: float = 0.15
    extrapolation: float = 0.30  # weight for penalty subtraction (not part of sum)


DEFAULT_WEIGHTS = ScoringWeightsV1()


@dataclass(slots=True)
class RankedCandidate:
    """A scored, ranked correlation candidate.

    Attributes:
        key: Correlation key (e.g. "internal.gnielinski").
        score: Total weighted score (higher = better recommendation).
        breakdown: Per-factor scores before weighting.
        weights_version: ScoringWeightsV1.version used.
    """

    key: str
    score: float
    breakdown: dict[str, float]
    weights_version: str


class RankingEngine:
    """Scores and ranks applicable correlation candidates using scoring v1."""

    def __init__(self, weights: ScoringWeightsV1 | None = None) -> None:
        self._w = weights or DEFAULT_WEIGHTS

    def rank(
        self, state: EngineeringState, methods: list[CorrelationMetadata]
    ) -> list[RankedCandidate]:
        """Return methods sorted by descending score."""
        candidates = [self._score(state, m) for m in methods]
        return sorted(candidates, key=lambda r: r.score, reverse=True)

    def _score(
        self, state: EngineeringState, method: CorrelationMetadata
    ) -> RankedCandidate:
        w = self._w
        factors = _compute_factors(state, method)

        total = (
            w.validity * factors["validity_fit"]
            + w.geometry * factors["geometry_match"]
            + w.regime * factors["regime_match"]
            + w.boundary * factors["boundary_match"]
            + w.corrections * factors["correction_score"]
            + w.pedigree * factors["pedigree"]
            + w.uncertainty * factors["uncertainty_score"]
            - w.extrapolation * factors["extrapolation_penalty"]
        )
        total = max(0.0, min(1.0, total))

        return RankedCandidate(
            key=method.key,
            score=round(total, 6),
            breakdown=factors,
            weights_version=w.version,
        )


# ---------------------------------------------------------------------------
# Factor computation — pure functions
# ---------------------------------------------------------------------------


def _compute_factors(
    state: EngineeringState, method: CorrelationMetadata
) -> dict[str, float]:
    return {
        "validity_fit": _validity_fit(state, method),
        "geometry_match": _geometry_match(state, method),
        "regime_match": _regime_match(state, method),
        "boundary_match": _boundary_match(state, method),
        "correction_score": _correction_score(state, method),
        "pedigree": _pedigree(method),
        "uncertainty_score": _uncertainty_score(method),
        "extrapolation_penalty": _extrapolation_penalty(state, method),
    }


def _validity_fit(state: EngineeringState, method: CorrelationMetadata) -> float:
    """Score highest at center of valid Re range, 0 at edges, clamped to [0, 1]."""
    re_min = method.validity.get("re_min")
    re_max = method.validity.get("re_max")
    re = state.reynolds

    if re_min is not None and re_max is not None:
        center = (re_min + re_max) / 2.0
        half = (re_max - re_min) / 2.0
        fit = 1.0 - abs(re - center) / half if half > 0 else 1.0
        return max(0.0, min(1.0, fit))

    if re_max is not None:
        # Only upper bound: score falls from 1.0 at 0 to 0 at re_max
        return max(0.0, min(1.0, 1.0 - re / re_max))

    if re_min is not None:
        # Only lower bound: score is 0 below re_min, rises to 1 well above
        return min(1.0, re / re_min) if re > 0 else 0.0

    return 1.0  # no range constraint


def _geometry_match(state: EngineeringState, method: CorrelationMetadata) -> float:
    required = method.validity.get("geometry_type")
    if required is None:
        return 1.0
    return 1.0 if required == state.geometry.geometry_type else 0.0


def _regime_match(state: EngineeringState, method: CorrelationMetadata) -> float:
    """Compare method's declared flow regime against inferred regime from Re."""
    re = state.reynolds
    geo = state.geometry.geometry_type

    if geo == "circular_tube":
        if re < RE_LAMINAR_MAX:
            inferred = "laminar"
        elif re > RE_TRANSITION_MAX:
            inferred = "turbulent"
        else:
            inferred = "transitional"
    else:
        # Flat plates and cylinders: use Re thresholds loosely
        inferred = "laminar" if re < RE_PLATE_TURBULENT else "turbulent"

    method_regime = (
        method.flow_regime
    )  # "all", "laminar", "turbulent", "transitional_turbulent", etc.

    if method_regime in ("all", ""):
        return 1.0
    if method_regime == inferred:
        return 1.0
    if method_regime == "transitional_turbulent" and inferred in (
        "transitional",
        "turbulent",
    ):
        return 1.0
    # Partial credit: method might still give valid results
    return 0.2


def _boundary_match(state: EngineeringState, method: CorrelationMetadata) -> float:
    method_bcs = method.boundary_conditions
    if not method_bcs:
        return 1.0
    return 1.0 if state.boundary.boundary_type in method_bcs else 0.5


def _correction_score(state: EngineeringState, method: CorrelationMetadata) -> float:
    """Higher score when available data matches corrections the method can use."""
    score = 0.5  # base
    if (
        method.key in _VISCOSITY_CORRECTION_KEYS
        and state.fluid.wall_viscosity is not None
    ):
        score += 0.25
    if method.key in _ENTRY_LENGTH_KEYS and state.flow.developing_length is not None:
        score += 0.25
    return min(1.0, score)


def _pedigree(method: CorrelationMetadata) -> float:
    """Source quality proxy based on publication year."""
    year = method.source.get("year", 1950)
    if year >= 1970:
        pedigree = 0.9
    elif year >= 1950:
        pedigree = 0.7
    else:
        pedigree = 0.5
    # Gnielinski and Petukhov are best-in-class for turbulent pipe flow
    # (lowest literature uncertainty, widest validation base). If new
    # correlations achieve similar standing, add them here with a source note.
    if method.key in ("internal.gnielinski", "internal.petukhov"):
        pedigree = min(1.0, pedigree + 0.1)
    return pedigree


def _uncertainty_score(method: CorrelationMetadata) -> float:
    """Lower documented uncertainty → higher score."""
    lit_unc = method.literature_uncertainty_pct
    if lit_unc is None:
        return 0.5
    if lit_unc <= 10:
        return 1.0
    if lit_unc <= 20:
        return 0.7
    return 0.4


def _extrapolation_penalty(
    state: EngineeringState, method: CorrelationMetadata
) -> float:
    """Penalty grows with distance outside the valid Re range."""
    penalty = 0.0
    re = state.reynolds
    re_max = method.validity.get("re_max")
    re_min = method.validity.get("re_min")

    if re_max is not None and re > re_max:
        over = (re - re_max) / re_max
        penalty += min(0.5, over)

    if re_min is not None and re_min > 0 and re < re_min:
        under = (re_min - re) / re_min
        penalty += min(0.5, under)

    return min(1.0, penalty)
