"""Tests for CorrelationRegistry loading and lookup."""

from __future__ import annotations

from pathlib import Path

import pytest

from htcie.core.registry import CorrelationRegistry

_DATA_DIR = Path(__file__).parents[2] / "data" / "correlations"


@pytest.fixture(scope="module")
def registry() -> CorrelationRegistry:
    reg = CorrelationRegistry()
    reg.load_from_dir(_DATA_DIR)
    return reg


def test_loads_all_correlations(registry: CorrelationRegistry) -> None:
    assert len(registry.all()) >= 10


def test_get_known_key(registry: CorrelationRegistry) -> None:
    meta = registry.get("internal.dittus_boelter")
    assert meta.key == "internal.dittus_boelter"
    assert meta.title != ""


def test_get_missing_key_raises(registry: CorrelationRegistry) -> None:
    """CorrelationRegistry.get() raises KeyError for unknown keys."""
    with pytest.raises(KeyError):
        registry.get("nonexistent_key_xyz")


def test_by_family_returns_subset(registry: CorrelationRegistry) -> None:
    internal = registry.by_family("convection_internal")
    assert len(internal) >= 4
    assert all(m.family == "convection_internal" for m in internal)


def test_by_family_unknown_returns_empty(registry: CorrelationRegistry) -> None:
    result = registry.by_family("nonexistent_family")
    assert result == []


def test_families_lists_expected(registry: CorrelationRegistry) -> None:
    families = registry.families()
    assert "convection_internal" in families
    assert "convection_external" in families
    assert "tube_banks" in families


def test_all_entries_have_required_fields(registry: CorrelationRegistry) -> None:
    for meta in registry.all():
        assert meta.key, f"{meta.key!r} has empty key"
        assert meta.source, f"{meta.key!r} missing source"
        assert meta.validity is not None, f"{meta.key!r} missing validity"
