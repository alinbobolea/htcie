"""Shared result types for correlation evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EvaluationResult:
    """Result of evaluating a single heat-transfer correlation.

    Attributes:
        key: Correlation identifier (e.g. ``"internal.gnielinski"``).
        output_name: Physical quantity produced (e.g. ``"nusselt"``).
        value: Computed numerical value of the output quantity.
        metadata: Supplementary inputs and flags recorded for traceability.
    """

    key: str
    output_name: str
    value: float
    metadata: dict[str, Any]
