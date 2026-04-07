"""Numerical evaluation of correlation candidates."""

from __future__ import annotations

from htcie.core.registry import CorrelationMetadata
from htcie.core.results import EvaluationResult
from htcie.core.state import EngineeringState
from htcie.domains import convection_external, convection_internal, tube_banks

# Re-export so existing importers of EvaluationResult from this module keep working.
__all__ = ["EvaluationResult", "EvaluationEngine"]

DOMAIN_MAP = {
    "convection_internal": convection_internal,
    "convection_external": convection_external,
    "tube_banks": tube_banks,
}


class EvaluationEngine:
    """Dispatches correlation evaluation to the appropriate domain module.

    The engine maps each correlation's ``family`` field to the corresponding
    domain module (``convection_internal``, ``convection_external``,
    ``tube_banks``). Each domain module exposes an ``evaluate(key, state)``
    function that returns an :class:`~htcie.core.results.EvaluationResult`.
    """

    def evaluate(
        self, state: EngineeringState, method: CorrelationMetadata
    ) -> EvaluationResult:
        module = DOMAIN_MAP.get(method.family)
        if module is None:
            raise NotImplementedError(f"No evaluator for family: {method.family}")
        return module.evaluate(method.key, state)  # type: ignore[attr-defined]
