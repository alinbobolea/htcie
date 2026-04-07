"""Tests for htcie.gui.main port resolution from environment variables."""

from __future__ import annotations

from unittest.mock import patch

import pytest


def test_run_reads_port_from_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """run() uses PORT env var when no explicit port argument is passed."""
    monkeypatch.setenv("PORT", "9999")
    monkeypatch.setenv("NICEGUI_STORAGE_SECRET", "test-secret")
    with (
        patch("htcie.gui.main.evaluate.setup"),
        patch("htcie.gui.main.methods.setup"),
        patch("htcie.gui.main.about.setup"),
        patch("htcie.gui.main.ui.run") as mock_run,
    ):
        import htcie.gui.main as gui_main

        gui_main.run()

    kwargs = mock_run.call_args.kwargs
    assert kwargs["port"] == 9999
    assert kwargs["show"] is False
    assert kwargs["storage_secret"] == "test-secret"


def test_run_uses_explicit_port_over_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Explicit port= argument takes precedence over PORT env var."""
    monkeypatch.setenv("PORT", "9999")
    with (
        patch("htcie.gui.main.evaluate.setup"),
        patch("htcie.gui.main.methods.setup"),
        patch("htcie.gui.main.about.setup"),
        patch("htcie.gui.main.ui.run") as mock_run,
    ):
        import htcie.gui.main as gui_main

        gui_main.run(port=7777)

    assert mock_run.call_args.kwargs["port"] == 7777


def test_run_defaults_port_to_8080_without_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Port defaults to 8080 when neither argument nor PORT env var is set."""
    monkeypatch.delenv("PORT", raising=False)
    with (
        patch("htcie.gui.main.evaluate.setup"),
        patch("htcie.gui.main.methods.setup"),
        patch("htcie.gui.main.about.setup"),
        patch("htcie.gui.main.ui.run") as mock_run,
    ):
        import htcie.gui.main as gui_main

        gui_main.run()

    assert mock_run.call_args.kwargs["port"] == 8080


def test_run_uses_default_storage_secret_without_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """storage_secret defaults to 'dev-secret-change-me' when NICEGUI_STORAGE_SECRET is not set."""
    monkeypatch.delenv("NICEGUI_STORAGE_SECRET", raising=False)
    with (
        patch("htcie.gui.main.evaluate.setup"),
        patch("htcie.gui.main.methods.setup"),
        patch("htcie.gui.main.about.setup"),
        patch("htcie.gui.main.ui.run") as mock_run,
    ):
        import htcie.gui.main as gui_main

        gui_main.run()

    assert mock_run.call_args.kwargs["storage_secret"] == "dev-secret-change-me"
