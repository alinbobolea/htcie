"""Shared evaluation pipeline.

Stages: applicability → evaluate → uncertainty → rank → confidence → explain → report.
"""

from __future__ import annotations

from htcie.core.applicability import ApplicabilityEngine
from htcie.core.evaluator import EvaluationEngine
from htcie.core.explain import build_explanation
from htcie.core.ranking import DEFAULT_WEIGHTS, RankingEngine
from htcie.core.registry import CorrelationRegistry
from htcie.core.state import EngineeringState
from htcie.core.uncertainty import (
    UncertaintyEngine,
    confidence_class,
    extrapolation_status,
    summarize_spread,
)
from htcie.reports.schema import HtcieReport


def run_evaluation(
    state: EngineeringState,
    registry: CorrelationRegistry,
) -> HtcieReport | None:
    """Run the full evaluation pipeline and return a serializable HtcieReport.

    Applies applicability filters, evaluates each eligible correlation,
    computes per-correlation uncertainty bands, ranks results, computes
    confidence, builds explanation, and packages the result as a complete
    audit object.

    Args:
        state: The canonical engineering state describing the problem.
        registry: Loaded correlation metadata registry.

    Returns:
        HtcieReport if at least one method is applicable, else None.
    """
    applicability = ApplicabilityEngine()
    evaluator = EvaluationEngine()
    ranker = RankingEngine()
    uncertainty_engine = UncertaintyEngine()

    all_methods = registry.all()
    app_result = applicability.evaluate(state, all_methods)

    if not app_result.applicable:
        return None

    # C5: Film-temperature advisory for external correlations.
    # Hilpert, Žukauskas, Churchill-Bernstein, Pohlhausen, turbulent plate all
    # require fluid properties evaluated at T_film = (T_wall + T_inf)/2. If
    # wall_temperature is not provided we cannot verify this.
    _EXTERNAL_FILM_TEMP_GEOMETRIES = frozenset({"cylinder_crossflow", "flat_plate"})
    pipeline_warnings: list[str] = []
    if (
        state.geometry.geometry_type in _EXTERNAL_FILM_TEMP_GEOMETRIES
        and state.boundary.wall_temperature is None
    ):
        pipeline_warnings.append(
            "Film temperature cannot be verified: wall_temperature not provided. "
            "External convection correlations require fluid properties evaluated at "
            "T_film = (T_wall + T_inf)/2. Results may be systematically biased if "
            "properties were not evaluated at film temperature."
        )

    evaluations = [evaluator.evaluate(state, m) for m in app_result.applicable]
    uncertainty_results = uncertainty_engine.compute(
        state, evaluations, app_result.applicable
    )
    uncertainty_by_key = {r.key: r for r in uncertainty_results}

    ranked = ranker.rank(state, app_result.applicable)
    spread = summarize_spread(evaluations)

    best = ranked[0]
    best_meta = registry.get(best.key)
    ext_status = extrapolation_status(state, best_meta)
    ext_warnings = ext_status["warnings"]
    confidence = confidence_class(spread, extrapolation_warnings=ext_warnings)

    explanation = build_explanation(
        best, best_meta, app_result.excluded, confidence, ext_warnings
    )

    return HtcieReport(
        input_state=state,
        warnings=pipeline_warnings,
        derived={
            "reynolds": state.reynolds,
            "prandtl": state.prandtl,
            "graetz": state.graetz,
            "entry_length_ratio": state.entry_length_ratio,
            "pitch_ratio_transverse": state.pitch_ratio_transverse,
            "pitch_ratio_longitudinal": state.pitch_ratio_longitudinal,
        },
        applicable=[m.key for m in app_result.applicable],
        excluded=[{"key": m.key, "reason": r} for m, r in app_result.excluded],
        evaluations=[
            {
                "key": e.key,
                "value": e.value,
                "metadata": e.metadata,
                "uncertainty_pct": uncertainty_by_key[e.key].uncertainty_pct,
                "h": uncertainty_by_key[e.key].h,
                "h_low": uncertainty_by_key[e.key].h_low,
                "h_high": uncertainty_by_key[e.key].h_high,
                "uncertainty_note": uncertainty_by_key[e.key].note,
            }
            for e in evaluations
        ],
        ranking=[
            {"key": r.key, "score": r.score, "breakdown": r.breakdown} for r in ranked
        ],
        spread=spread,
        confidence=confidence,
        explanation=explanation,
        scoring_weights_version=DEFAULT_WEIGHTS.version,
    )
