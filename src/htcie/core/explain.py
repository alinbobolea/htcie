"""Structured explanation builder for htcie evaluation results."""

from __future__ import annotations

from dataclasses import dataclass

from htcie.core.ranking import RankedCandidate
from htcie.core.registry import CorrelationMetadata


@dataclass
class Explanation:
    """Structured explanation of an htcie evaluation result.

    Attributes:
        best_method: Key of the top-ranked correlation.
        best_score: Numeric score of the top-ranked correlation.
        score_breakdown: Per-factor scores for the best method.
        why_applicable: Reasons why the best method was applicable.
            Currently a single-item list populated by :func:`build_explanation`
            with a generic sentence covering Re, Pr, and geometry.
        why_others_excluded: List of (key, reason) tuples for excluded methods.
        key_assumptions: Key assumptions of the best method.
        confidence_class: "high", "medium", or "low".
        extrapolation_warnings: List of extrapolation warning strings.
        recommendation_note: One-sentence recommendation summary.
    """

    best_method: str
    best_score: float
    score_breakdown: dict[str, float]
    why_applicable: list[str]
    why_others_excluded: list[tuple[str, str]]
    key_assumptions: list[str]
    confidence_class: str
    extrapolation_warnings: list[str]
    recommendation_note: str

    def to_text(self) -> str:
        """Return a human-readable multi-line explanation.

        Sections are rendered in this order:

        1. Recommended method name and score
        2. Per-factor score breakdown (always present)
        3. Confidence class
        4. Extrapolation warnings (omitted when empty)
        5. Key assumptions (omitted when empty)
        6. Excluded methods with reasons (omitted when empty)
        7. One-sentence recommendation note

        Returns:
            Newline-joined string suitable for printing or embedding in a
            Markdown code block.
        """
        lines = [
            f"Recommended method: {self.best_method}",
            f"Score: {self.best_score:.3f}",
            "",
            "Score breakdown:",
        ]
        for factor, value in self.score_breakdown.items():
            lines.append(f"  {factor}: {value:.3f}")
        lines.append("")
        lines.append(f"Confidence: {self.confidence_class}")
        if self.extrapolation_warnings:
            lines.append("Extrapolation warnings:")
            for w in self.extrapolation_warnings:
                lines.append(f"  - {w}")
        if self.key_assumptions:
            lines.append("Key assumptions:")
            for a in self.key_assumptions:
                lines.append(f"  - {a}")
        if self.why_others_excluded:
            lines.append("Excluded methods:")
            for key, reason in self.why_others_excluded:
                lines.append(f"  {key}: {reason}")
        lines.append("")
        lines.append(self.recommendation_note)
        return "\n".join(lines)


def build_explanation(
    best: RankedCandidate,
    best_meta: CorrelationMetadata,
    excluded: list[tuple[CorrelationMetadata, str]],
    confidence: str,
    extrapolation_warnings: list[str],
) -> Explanation:
    """Build a structured :class:`Explanation` from pipeline evaluation components.

    Args:
        best: Top-ranked candidate from :class:`~htcie.core.ranking.RankingEngine`.
        best_meta: Full metadata for the best candidate.
        excluded: ``(metadata, reason)`` pairs from
            :class:`~htcie.core.applicability.ApplicabilityEngine`.
        confidence: Confidence class string (``"high"``, ``"medium"``, or
            ``"low"``) from :func:`~htcie.core.uncertainty.confidence_class`.
        extrapolation_warnings: Warning strings from
            :func:`~htcie.core.uncertainty.extrapolation_status`.

    Returns:
        Populated :class:`Explanation` including the recommendation note and
        up to three key assumptions from the best method's metadata.
    """
    recommendation_note = (
        f"Use {best.key} — highest score ({best.score:.3f})"
        f" for the given operating conditions."
    )
    return Explanation(
        best_method=best.key,
        best_score=best.score,
        score_breakdown=best.breakdown,
        why_applicable=[
            f"{best.key} is applicable for the given Re, Pr, and geometry."
        ],
        why_others_excluded=[(m.key, r) for m, r in excluded],
        key_assumptions=best_meta.assumptions[:3],
        confidence_class=confidence,
        extrapolation_warnings=extrapolation_warnings,
        recommendation_note=recommendation_note,
    )


def explain_recommendation(best: RankedCandidate) -> str:
    """Return a plain-text summary of the top-ranked candidate.

    This is a lightweight alternative to :func:`build_explanation` for callers
    that only need the method key, total score, and factor breakdown as text —
    without constructing an :class:`Explanation` object.  Used by
    ``api/main.py`` and ``cli/main.py`` where the full structured explanation
    is not required.

    Args:
        best: Top-ranked candidate from :class:`~htcie.core.ranking.RankingEngine`.

    Returns:
        Multi-line string with the method key, total score, and per-factor
        breakdown.
    """
    lines = [
        f"Best method: {best.key}",
        f"Total score: {best.score:.3f}",
        "Breakdown:",
    ]
    for factor, value in best.breakdown.items():
        lines.append(f"  {factor}: {value:.3f}")
    return "\n".join(lines)
