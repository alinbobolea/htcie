"""POST /evaluate endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from htcie.api import dependencies
from htcie.api.schemas import EvaluateRequest
from htcie.core.applicability import ApplicabilityEngine
from htcie.core.pipeline import run_evaluation

router = APIRouter(prefix="/evaluate", tags=["evaluate"])


@router.post("")
def evaluate(request: EvaluateRequest) -> dict:
    """Run evaluation pipeline and return full result."""
    report = run_evaluation(request.state, dependencies.registry)
    if report is None:
        # No applicable methods — run applicability to return diagnostic excluded list
        app = ApplicabilityEngine().evaluate(request.state, dependencies.registry.all())
        return {
            "applicable": [],
            "excluded": [{"key": m.key, "reason": r} for m, r in app.excluded],
            "confidence": "low",
            "explanation": (
                "No methods are applicable for the given operating conditions."
            ),
        }
    return report.to_dict()
