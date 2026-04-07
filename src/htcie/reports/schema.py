"""HtcieReport — the full audit object for one evaluation run.

:class:`HtcieReport` is the single output of ``run_evaluation``. It captures
every decision made by the pipeline so the result is fully reproducible and
auditable without re-running the engine.

Use :meth:`HtcieReport.to_dict` to obtain a JSON-serialisable dict, or pass
the report to the serializer helpers in :mod:`htcie.reports.serializers` to
write JSON, Markdown, or HTML files.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

import htcie
from htcie.core.explain import Explanation
from htcie.core.state import EngineeringState


class HtcieReport(BaseModel):
    """Complete, serializable audit record of one htcie evaluation.

    Every field is included so the report is self-contained — no
    external state is required to re-interpret the output.

    Complex field shapes:

    - ``derived`` — dimensionless groups computed from the state:
      ``reynolds``, ``prandtl``, ``graetz``, ``entry_length_ratio``,
      ``pitch_ratio_transverse``, ``pitch_ratio_longitudinal``.
      Fields that are not applicable for the geometry (e.g. ``graetz``
      for external flow) are ``None``.
    - ``evaluations`` — one entry per applicable correlation, each a dict
      with ``key``, ``value`` (Nu), ``metadata``, ``uncertainty_pct``,
      ``h``, ``h_low``, ``h_high``, and ``uncertainty_note``.
    - ``excluded`` — one entry per filtered-out correlation:
      ``{"key": str, "reason": str}``.
    - ``ranking`` — correlations sorted by descending score, each entry
      ``{"key": str, "score": float, "breakdown": dict[str, float]}``.
    - ``spread`` — inter-method statistics: ``count``, ``mean``, ``stdev``,
      ``relative_spread``.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    engine_version: str = Field(default_factory=lambda: htcie.__version__)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime(
            "%Y-%m-%d, %H:%M:%S UTC"
        )
    )
    input_state: EngineeringState
    derived: dict[str, Any]  # See class docstring for keys
    applicable: list[str]  # keys of applicable correlations
    excluded: list[dict[str, str]]  # [{"key": ..., "reason": ...}]
    evaluations: list[dict[str, Any]]  # See class docstring for per-entry shape
    ranking: list[dict[str, Any]]  # [{"key": ..., "score": ..., "breakdown": ...}]
    spread: dict[str, Any]  # count, mean, stdev, relative_spread
    confidence: str  # "high", "medium", "low"
    # advisory messages (film temperature checks, etc.)
    warnings: list[str] = Field(default_factory=list)
    explanation: Explanation
    scoring_weights_version: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict representation of this report.

        The ``explanation`` sub-dict expands the :class:`~htcie.core.explain.Explanation`
        dataclass inline.  ``why_others_excluded`` is converted from a list of
        ``(key, reason)`` tuples to a list of ``{"key": ..., "reason": ...}``
        dicts, and a rendered ``"text"`` key is added via
        :meth:`~htcie.core.explain.Explanation.to_text`.
        """
        return {
            "engine_version": self.engine_version,
            "timestamp": self.timestamp,
            "input_state": self.input_state.model_dump(),
            "derived": self.derived,
            "applicable": self.applicable,
            "excluded": self.excluded,
            "evaluations": self.evaluations,
            "ranking": self.ranking,
            "spread": self.spread,
            "confidence": self.confidence,
            "warnings": self.warnings,
            "explanation": {
                "best_method": self.explanation.best_method,
                "best_score": self.explanation.best_score,
                "score_breakdown": self.explanation.score_breakdown,
                "why_applicable": self.explanation.why_applicable,
                "why_others_excluded": [
                    {"key": k, "reason": r}
                    for k, r in self.explanation.why_others_excluded
                ],
                "key_assumptions": self.explanation.key_assumptions,
                "confidence_class": self.explanation.confidence_class,
                "extrapolation_warnings": self.explanation.extrapolation_warnings,
                "recommendation_note": self.explanation.recommendation_note,
                "text": self.explanation.to_text(),
            },
            "scoring_weights_version": self.scoring_weights_version,
        }
