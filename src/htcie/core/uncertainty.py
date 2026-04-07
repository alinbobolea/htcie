"""Uncertainty, confidence, and extrapolation heuristics."""

from __future__ import annotations

import re
from dataclasses import dataclass
from statistics import mean, pstdev

from htcie.core.registry import CorrelationMetadata
from htcie.core.results import EvaluationResult
from htcie.core.state import EngineeringState


def summarize_spread(results: list[EvaluationResult]) -> dict:
    """Compute inter-method spread statistics over a set of evaluation results.

    Returns:
        dict with keys:

        - ``count``: number of results
        - ``mean``: arithmetic mean of the output values
        - ``stdev``: population standard deviation :math:`\\sigma`
        - ``relative_spread``: :math:`\\sigma / \\bar{x}` (coefficient of
          variation), or ``None`` if mean is zero
    """
    values = [r.value for r in results]
    if not values:
        return {"count": 0, "mean": None, "stdev": None, "relative_spread": None}
    avg = mean(values)
    stdev = pstdev(values) if len(values) > 1 else 0.0
    rel = (stdev / avg) if avg else None
    return {"count": len(values), "mean": avg, "stdev": stdev, "relative_spread": rel}


def confidence_class(
    spread_summary: dict,
    extrapolation_warnings: list[str] | None = None,
) -> str:
    """Classify confidence as 'high', 'medium', or 'low'.

    Args:
        spread_summary: Output of summarize_spread().
        extrapolation_warnings: Optional list of extrapolation warning strings.
            Warnings produced by extrapolation_status() embed the ratio as
            'ratio X.XX'; ratios >= 1.2 indicate significant extrapolation.

    Returns:
        'high': spread < 5% AND no extrapolation warnings.
        'medium': spread < 15% OR mild extrapolation (max ratio < 1.2).
        'low': spread >= 15% OR significant extrapolation (max ratio >= 1.2).
    """
    warnings = extrapolation_warnings or []
    rel = spread_summary.get("relative_spread")
    max_ratio = _max_extrapolation_ratio(warnings)

    if rel is None:
        return "low"
    if rel < 0.05 and not warnings:
        return "high"
    if rel < 0.15 and max_ratio < 1.2:
        return "medium"
    return "low"


def _max_extrapolation_ratio(warnings: list[str]) -> float:
    """Parse the maximum extrapolation ratio from warning strings.

    Warnings from extrapolation_status() include 'ratio X.XX'. Falls back
    to 1.0 (no extrapolation) when no ratio can be parsed, and to a
    conservative 1.5 when a warning exists but has no parseable ratio.
    """
    if not warnings:
        return 1.0

    ratios: list[float] = []
    for w in warnings:
        match = re.search(r"ratio\s+([0-9]+\.[0-9]+)", w)
        if match:
            ratios.append(float(match.group(1)))
    # If warnings present but none parseable, treat as significant
    return max(ratios) if ratios else 1.5


def extrapolation_status(state: EngineeringState, method: CorrelationMetadata) -> dict:
    """Return extrapolation details for one method vs. the current state.

    Args:
        state: Current engineering state with Re and Pr computed fields.
        method: Correlation metadata containing validity bounds.

    Returns:
        dict with keys:

        - ``extrapolated``: ``True`` if Re or Pr is outside the valid range.
        - ``re_fraction``: ratio measuring how far Re is outside range —
          ``re/re_max`` if above, ``re_min/re`` if below, ``1.0`` if within.
          ``None`` when the correlation has no Re bounds.
        - ``pr_fraction``: same logic for Pr. ``None`` when no Pr bounds.
        - ``warnings``: human-readable warning strings, one per violated bound.
    """
    validity = method.validity
    re = state.reynolds
    pr = state.prandtl

    re_fraction: float | None = None
    pr_fraction: float | None = None
    warnings: list[str] = []
    extrapolated = False

    re_min = validity.get("re_min")
    re_max = validity.get("re_max")
    pr_min = validity.get("pr_min")
    pr_max = validity.get("pr_max")

    if re_min is not None or re_max is not None:
        if re_max is not None and re > re_max:
            re_fraction = re / re_max
            extrapolated = True
            warnings.append(
                f"Re={re:.1f} exceeds re_max={re_max:.1f} (ratio {re_fraction:.2f})"
            )
        elif re_min is not None and re < re_min:
            re_fraction = re_min / re
            extrapolated = True
            warnings.append(
                f"Re={re:.1f} is below re_min={re_min:.1f} (ratio {re_fraction:.2f})"
            )
        else:
            re_fraction = 1.0

    if pr_min is not None or pr_max is not None:
        if pr_max is not None and pr > pr_max:
            pr_fraction = pr / pr_max
            extrapolated = True
            warnings.append(
                f"Pr={pr:.3f} exceeds pr_max={pr_max:.3f} (ratio {pr_fraction:.2f})"
            )
        elif pr_min is not None and pr < pr_min:
            pr_fraction = pr_min / pr
            extrapolated = True
            warnings.append(
                f"Pr={pr:.3f} is below pr_min={pr_min:.3f} (ratio {pr_fraction:.2f})"
            )
        else:
            pr_fraction = 1.0

    return {
        "extrapolated": extrapolated,
        "re_fraction": re_fraction,
        "pr_fraction": pr_fraction,
        "warnings": warnings,
    }


@dataclass(slots=True)
class UncertaintyResult:
    """Per-correlation uncertainty band result.

    Attributes:
        key: Correlation key matching ``EvaluationResult.key``.
        value: Evaluated Nu (same as ``EvaluationResult.value``).
        h: Heat transfer coefficient ``Nu × k / L_char`` [W/m²·K].
        uncertainty_pct: Stated literature uncertainty in percent, or None.
        h_low: ``h × (1 - pct/100)``, or None when band is suppressed.
        h_high: ``h × (1 + pct/100)``, or None when band is suppressed.
        extrapolated: True when Re or Pr is outside the validity range.
        note: Empty string when band is valid; reason string when suppressed
            or clamped.
    """

    key: str
    value: float
    h: float
    uncertainty_pct: float | None
    h_low: float | None
    h_high: float | None
    extrapolated: bool
    note: str


class UncertaintyEngine:
    """Computes per-correlation uncertainty bands from stated literature uncertainty.

    The band is a flat ±p% interval around the computed heat transfer
    coefficient h, where p = ``literature_uncertainty_pct`` from the YAML
    metadata.  The band is suppressed (``h_low=None``, ``h_high=None``) when
    operating outside the correlation's validity range, when the stated
    uncertainty is not physically meaningful, or when the evaluated value is
    non-positive.
    """

    def compute(
        self,
        state: EngineeringState,
        evaluations: list[EvaluationResult],
        methods: list[CorrelationMetadata],
    ) -> list[UncertaintyResult]:
        """Return one UncertaintyResult per evaluation, in the same order.

        Args:
            state: Current engineering state.
            evaluations: Evaluated correlation results.
            methods: Correlation metadata for applicable correlations.

        Returns:
            List of UncertaintyResult objects, length equals len(evaluations).
        """
        if not evaluations:
            return []
        meta_by_key: dict[str, CorrelationMetadata] = {m.key: m for m in methods}
        return [self._compute_one(state, ev, meta_by_key[ev.key]) for ev in evaluations]

    def _compute_one(
        self,
        state: EngineeringState,
        evaluation: EvaluationResult,
        method: CorrelationMetadata,
    ) -> UncertaintyResult:
        k = state.fluid.thermal_conductivity
        L = state.geometry.hydraulic_diameter or state.geometry.characteristic_length
        h = evaluation.value * k / L

        pct = method.literature_uncertainty_pct
        ext = extrapolation_status(state, method)
        extrapolated = ext["extrapolated"]

        if pct is None:
            return UncertaintyResult(
                key=evaluation.key,
                value=evaluation.value,
                h=h,
                uncertainty_pct=None,
                h_low=None,
                h_high=None,
                extrapolated=extrapolated,
                note="No stated uncertainty in source",
            )

        if pct <= 0:
            return UncertaintyResult(
                key=evaluation.key,
                value=evaluation.value,
                h=h,
                uncertainty_pct=pct,
                h_low=None,
                h_high=None,
                extrapolated=extrapolated,
                note="Uncertainty of ≤0% is not physically meaningful",
            )

        if extrapolated:
            return UncertaintyResult(
                key=evaluation.key,
                value=evaluation.value,
                h=h,
                uncertainty_pct=pct,
                h_low=None,
                h_high=None,
                extrapolated=True,
                note="Band suppressed: operating outside validity range",
            )

        if h <= 0:
            return UncertaintyResult(
                key=evaluation.key,
                value=evaluation.value,
                h=h,
                uncertainty_pct=pct,
                h_low=None,
                h_high=None,
                extrapolated=False,
                note="Band suppressed: evaluated value ≤ 0",
            )

        h_low = h * (1.0 - pct / 100.0)
        h_high = h * (1.0 + pct / 100.0)
        note = ""

        if pct > 100.0:
            h_low = max(0.0, h_low)
            note = "h_low clamped to 0"

        return UncertaintyResult(
            key=evaluation.key,
            value=evaluation.value,
            h=h,
            uncertainty_pct=pct,
            h_low=h_low,
            h_high=h_high,
            extrapolated=False,
            note=note,
        )
