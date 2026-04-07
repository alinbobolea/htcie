"""Tests for the dual-source correlation loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from htcie.core.loader import _PACKAGE_DATA_DIR, build_registry
from htcie.core.registry import CorrelationRegistry


def test_package_data_dir_exists() -> None:
    """Packaged data directory must be present and contain YAML files."""
    assert _PACKAGE_DATA_DIR.is_dir()
    yamls = list(_PACKAGE_DATA_DIR.rglob("*.yaml"))
    assert len(yamls) >= 13


def test_build_registry_loads_packaged_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """build_registry() with no env var loads all packaged correlations."""
    monkeypatch.delenv("HTCIE_DATA_DIR", raising=False)
    registry = build_registry()
    assert len(registry.all()) >= 13


def test_build_registry_empty_env_var_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty HTCIE_DATA_DIR is treated as unset — only packaged data loads."""
    monkeypatch.setenv("HTCIE_DATA_DIR", "")
    registry = build_registry()
    assert len(registry.all()) >= 13


def test_build_registry_external_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """External dir overrides a packaged entry on key collision."""
    override_yaml = tmp_path / "convection_internal" / "gnielinski.yaml"
    override_yaml.parent.mkdir(parents=True)
    override_yaml.write_text(
        "key: internal.gnielinski\n"
        "family: convection_internal\n"
        "title: 'Custom Override'\n"
        "output: Nu\n"
        "flow_regime: all\n"
        "source:\n"
        "  authors: ['test']\n"
        "  year: 2024\n"
        "  title: 'test'\n"
        "  journal: 'test'\n"
        "assumptions: []\n"
        "notes: []\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HTCIE_DATA_DIR", str(tmp_path))
    registry = build_registry()
    assert registry.get("internal.gnielinski").title == "Custom Override"


def test_build_registry_external_adds_new_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """External dir can introduce a new correlation key alongside packaged ones."""
    new_yaml = tmp_path / "custom_correlation.yaml"
    new_yaml.write_text(
        "key: custom.my_correlation\n"
        "family: convection_internal\n"
        "title: 'My Custom Correlation'\n"
        "output: Nu\n"
        "flow_regime: all\n"
        "source:\n"
        "  authors: ['test']\n"
        "  year: 2024\n"
        "  title: 'test'\n"
        "  journal: 'test'\n"
        "assumptions: []\n"
        "notes: []\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HTCIE_DATA_DIR", str(tmp_path))
    registry = build_registry()
    assert registry.get("custom.my_correlation").title == "My Custom Correlation"
    # Packaged correlations still present
    assert len(registry.all()) >= 14


def test_build_registry_packaged_keys_match_external(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: packaged key set must equal the external data/correlations/ set."""
    external_dir = Path(__file__).parents[2] / "data" / "correlations"
    monkeypatch.delenv("HTCIE_DATA_DIR", raising=False)

    packaged_registry = build_registry()

    external_registry = CorrelationRegistry()
    external_registry.load_from_dir(external_dir)

    packaged_keys = {m.key for m in packaged_registry.all()}
    external_keys = {m.key for m in external_registry.all()}
    assert packaged_keys == external_keys, (
        f"Key mismatch — packaged only: {packaged_keys - external_keys!r}, "
        f"external only: {external_keys - packaged_keys!r}"
    )
