"""Correlation metadata loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class CorrelationMetadata(BaseModel):
    """Metadata for a single heat-transfer correlation loaded from a YAML file.

    Attributes:
        key: Dot-namespaced identifier, e.g. ``"internal.gnielinski"``.
        family: Domain family, e.g. ``"convection_internal"``.
        title: Human-readable name including author and year.
        output: Physical quantity produced (typically ``"Nu"``).
        formula_latex: LaTeX string of the primary correlation formula.
        flow_regime: Applicable regime: ``"laminar"``, ``"turbulent"``,
            ``"transitional_turbulent"``, or ``"all"``.
        boundary_conditions: List of applicable boundary condition types,
            e.g. ``["constant_wall_temperature", "constant_heat_flux"]``.
        required_inputs: Dimensionless groups or inputs required by the
            correlation, e.g. ``["Reynolds", "Prandtl"]``.
        validity: Dict of bounds used for applicability filtering, e.g.
            ``{"re_min": 3000, "re_max": 5000000, "geometry_type": "circular_tube"}``.
        literature_uncertainty_pct: Stated accuracy from the source publication,
            in percent, or None if not reported.
        assumptions: List of stated assumptions (smooth tube, fully developed
            flow, etc.) for traceability.
        source: Bibliographic reference dict with keys ``authors``, ``year``,
            ``title``, ``journal``, ``doi``.
        notes: List of implementation or usage notes for this correlation.
    """

    key: str
    family: str
    title: str
    output: str
    formula_latex: str = ""
    flow_regime: str = "all"
    boundary_conditions: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    validity: dict[str, Any] = Field(default_factory=dict)
    literature_uncertainty_pct: float | None = None
    assumptions: list[str] = Field(default_factory=list)
    source: dict[str, Any] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class CorrelationRegistry:
    """In-memory store of correlation metadata loaded from YAML files.

    Load the registry once at startup via :meth:`load_from_dir`, then pass it
    to the pipeline or individual engines. The registry is intentionally
    stateless after loading — all correlation definitions live in
    ``data/correlations/`` YAML files, not in Python code.
    """

    def __init__(self) -> None:
        self._items: dict[str, CorrelationMetadata] = {}

    def load_from_dir(self, path: str | Path) -> None:
        """Recursively load all ``*.yaml`` files from *path* into the registry.

        Files are processed in sorted order so loading is deterministic.
        Each file must contain a single YAML document that validates against
        :class:`CorrelationMetadata`.

        Args:
            path: Root directory containing correlation YAML files (may be
                nested in subdirectories).

        Raises:
            pydantic.ValidationError: If a YAML file fails schema validation.
        """
        base = Path(path)
        for yaml_file in sorted(base.rglob("*.yaml")):
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            meta = CorrelationMetadata.model_validate(data)
            self._items[meta.key] = meta

    def get(self, key: str) -> CorrelationMetadata:
        """Return metadata for *key*, raising ``KeyError`` if not found."""
        return self._items[key]

    def all(self) -> list[CorrelationMetadata]:
        """Return all loaded correlations in insertion order."""
        return list(self._items.values())

    def by_family(self, family: str) -> list[CorrelationMetadata]:
        """Return all correlations in the given family."""
        return [m for m in self._items.values() if m.family == family]

    def families(self) -> list[str]:
        """Return sorted list of unique families."""
        return sorted({m.family for m in self._items.values()})
