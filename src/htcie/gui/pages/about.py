"""About page."""

from __future__ import annotations

from nicegui import ui

import htcie


def setup() -> None:
    """Register the about page."""

    @ui.page("/about")
    def about_page() -> None:
        ui.label("About htcie").classes("text-2xl font-bold")
        ui.label(f"Version: {htcie.__version__}")
        ui.separator()
        ui.label(
            "htcie is an open-source Python library and web application for "
            "transparent, "
            "deterministic, API-first correlation decision-making for single-phase "
            "convection heat transfer."
        )
        ui.label("License: GNU AGPL v3")
