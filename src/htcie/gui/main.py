"""NiceGUI entry point for htcie."""

from __future__ import annotations

import os
import sys

from nicegui import ui

from htcie.gui.pages import about, evaluate, methods


def run(port: int | None = None, reload: bool = False) -> None:
    """Launch the htcie NiceGUI web interface.

    Args:
        port: TCP port to listen on. When ``None``, the ``PORT`` environment
            variable is read (Render.com injects this automatically). Falls
            back to 8080 for local development.
        reload: Enable hot-reload for development. Always ``False`` in
            production.
    """
    if port is None:
        port = int(os.environ.get("PORT", "8080"))
    storage_secret = os.environ.get("NICEGUI_STORAGE_SECRET", "dev-secret-change-me")
    evaluate.setup()
    methods.setup()
    about.setup()
    try:
        ui.run(
            title="htcie",
            port=port,
            reload=reload,
            show=False,
            storage_secret=storage_secret,
        )
    except KeyboardInterrupt:
        sys.exit(0)
