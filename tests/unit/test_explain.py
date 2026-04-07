"""Tests for explanation builder."""

from __future__ import annotations

import pytest

from htcie.core.explain import Explanation, build_explanation, explain_recommendation
from htcie.core.ranking import RankedCandidate
from htcie.core.registry import CorrelationMetadata


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_ranked(
    key: str = "internal.gnielinski", score: float = 0.8
) -> RankedCandidate:
    return RankedCandidate(
        key=key,
        score=score,
        breakdown={
            "validity_fit": 0.9,
            "geometry_match": 1.0,
            "regime_match": 1.0,
            "boundary_match": 1.0,
            "correction_score": 0.5,
            "pedigree": 0.9,
            "uncertainty_score": 1.0,
            "extrapolation_penalty": 0.0,
        },
        weights_version="v1",
    )


def make_meta(key: str = "internal.gnielinski") -> CorrelationMetadata:
    return CorrelationMetadata(
        key=key,
        family="convection_internal",
        title="Gnielinski (1976)",
        output="Nu",
        assumptions=["Smooth tube", "Fully developed flow"],
        source={"year": 1976},
    )


# ---------------------------------------------------------------------------
# build_explanation tests
# ---------------------------------------------------------------------------


def test_build_explanation_returns_explanation() -> None:
    ranked = make_ranked()
    meta = make_meta()
    exp = build_explanation(
        ranked, meta, excluded=[], confidence="high", extrapolation_warnings=[]
    )
    assert isinstance(exp, Explanation)
    assert exp.best_method == "internal.gnielinski"
    assert exp.confidence_class == "high"


def test_build_explanation_score() -> None:
    ranked = make_ranked(score=0.75)
    meta = make_meta()
    exp = build_explanation(
        ranked, meta, excluded=[], confidence="medium", extrapolation_warnings=[]
    )
    assert exp.best_score == pytest.approx(0.75)


def test_build_explanation_excluded() -> None:
    ranked = make_ranked()
    meta = make_meta()
    other_meta = make_meta(key="internal.dittus_boelter")
    exp = build_explanation(
        ranked,
        meta,
        excluded=[(other_meta, "Re out of range")],
        confidence="high",
        extrapolation_warnings=[],
    )
    assert len(exp.why_others_excluded) == 1
    assert exp.why_others_excluded[0][0] == "internal.dittus_boelter"
    assert exp.why_others_excluded[0][1] == "Re out of range"


def test_build_explanation_assumptions_capped() -> None:
    """build_explanation takes at most 3 assumptions."""
    meta = make_meta()
    meta = CorrelationMetadata(
        key="internal.gnielinski",
        family="convection_internal",
        title="Gnielinski (1976)",
        output="Nu",
        assumptions=["A1", "A2", "A3", "A4", "A5"],
        source={"year": 1976},
    )
    ranked = make_ranked()
    exp = build_explanation(
        ranked, meta, excluded=[], confidence="high", extrapolation_warnings=[]
    )
    assert len(exp.key_assumptions) == 3


def test_build_explanation_extrapolation_warnings() -> None:
    ranked = make_ranked()
    meta = make_meta()
    exp = build_explanation(
        ranked,
        meta,
        excluded=[],
        confidence="low",
        extrapolation_warnings=["Re=100000 exceeds re_max=50000 (ratio 2.00)"],
    )
    assert len(exp.extrapolation_warnings) == 1
    assert exp.confidence_class == "low"


# ---------------------------------------------------------------------------
# Explanation.to_text tests
# ---------------------------------------------------------------------------


def test_explanation_to_text() -> None:
    ranked = make_ranked()
    meta = make_meta()
    exp = build_explanation(
        ranked, meta, excluded=[], confidence="high", extrapolation_warnings=[]
    )
    text = exp.to_text()
    assert "internal.gnielinski" in text
    assert "Score" in text


def test_explanation_to_text_contains_confidence() -> None:
    ranked = make_ranked()
    meta = make_meta()
    exp = build_explanation(
        ranked, meta, excluded=[], confidence="medium", extrapolation_warnings=[]
    )
    text = exp.to_text()
    assert "medium" in text


def test_explanation_to_text_with_warnings() -> None:
    ranked = make_ranked()
    meta = make_meta()
    exp = build_explanation(
        ranked,
        meta,
        excluded=[],
        confidence="low",
        extrapolation_warnings=["Re exceeds re_max (ratio 2.00)"],
    )
    text = exp.to_text()
    assert "Extrapolation" in text
    assert "ratio 2.00" in text


def test_explanation_to_text_with_excluded() -> None:
    ranked = make_ranked()
    meta = make_meta()
    other = make_meta(key="internal.dittus_boelter")
    exp = build_explanation(
        ranked,
        meta,
        excluded=[(other, "outside valid Re range")],
        confidence="high",
        extrapolation_warnings=[],
    )
    text = exp.to_text()
    assert "internal.dittus_boelter" in text
    assert "outside valid Re range" in text


# ---------------------------------------------------------------------------
# explain_recommendation backward-compat tests
# ---------------------------------------------------------------------------


def test_explain_recommendation_backward_compat() -> None:
    ranked = make_ranked()
    text = explain_recommendation(ranked)
    assert "internal.gnielinski" in text
    assert "Score" in text or "score" in text.lower()


def test_explain_recommendation_includes_breakdown() -> None:
    ranked = make_ranked()
    text = explain_recommendation(ranked)
    assert "validity_fit" in text
