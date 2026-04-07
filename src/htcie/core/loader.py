"""Dual-source correlation loader.

Loads packaged correlations first, then overlays an optional external directory
(controlled by ``HTCIE_DATA_DIR``) on key collision.  The external directory
always wins, enabling per-deployment overrides or private/pro correlations
while keeping the package self-contained.
"""

from __future__ import annotations

import os
from pathlib import Path

from htcie.core.registry import CorrelationRegistry

# Mirrors the renderer.py pattern: Path(__file__).parent / ...
# src/htcie/core/loader.py  →  src/htcie/data/correlations/
_PACKAGE_DATA_DIR: Path = Path(__file__).parent.parent / "data" / "correlations"


def build_registry() -> CorrelationRegistry:
    """Return a :class:`~htcie.core.registry.CorrelationRegistry` from both sources.

    Loading order:

    1. Packaged YAML files at ``src/htcie/data/correlations/`` (always present).
    2. External directory from the ``HTCIE_DATA_DIR`` environment variable,
       if set and non-empty.  External entries overwrite packaged entries on
       key collision, allowing pro or per-deployment overrides.

    Returns:
        A fully loaded :class:`~htcie.core.registry.CorrelationRegistry`.
    """
    registry = CorrelationRegistry()
    registry.load_from_dir(_PACKAGE_DATA_DIR)

    external = os.environ.get("HTCIE_DATA_DIR", "").strip()
    if external:
        registry.load_from_dir(external)

    return registry
