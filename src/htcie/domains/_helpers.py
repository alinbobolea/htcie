"""Shared helpers for domain evaluator modules."""

from __future__ import annotations

from htcie.core.state import EngineeringState


def require_re_pr(state: EngineeringState) -> tuple[float, float]:
    """Extract and validate :math:`Re` and :math:`Pr` from *state*.

    Returns:
        ``(reynolds, prandtl)`` tuple.

    Raises:
        ValueError: If either dimensionless number is non-positive.
    """
    re = state.reynolds
    pr = state.prandtl
    if re <= 0:
        raise ValueError(f"Reynolds number must be positive, got {re}")
    if pr <= 0:
        raise ValueError(f"Prandtl number must be positive, got {pr}")
    return re, pr
