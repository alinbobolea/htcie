"""Methods browser page."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from htcie.core.loader import build_registry


def setup() -> None:
    """Register the methods browser page."""

    @ui.page("/methods")
    def methods_page() -> None:
        ui.label("Correlation Methods Browser").classes("text-2xl font-bold")

        registry = build_registry()
        all_methods = sorted(registry.all(), key=lambda m: m.key)

        families = ["All"] + sorted({m.family for m in all_methods})
        family_filter = ui.select(families, value="All", label="Filter by family")

        table_container = ui.column().classes("w-full")

        def render_table(family: str) -> None:
            table_container.clear()
            filtered = (
                all_methods
                if family == "All"
                else [m for m in all_methods if m.family == family]
            )
            with table_container:
                columns: list[dict[str, Any]] = [
                    {"name": "key", "label": "Key", "field": "key", "sortable": True},
                    {"name": "title", "label": "Title", "field": "title"},
                    {"name": "family", "label": "Family", "field": "family"},
                    {"name": "regime", "label": "Regime", "field": "regime"},
                    {"name": "re_range", "label": "Re Range", "field": "re_range"},
                ]
                rows = [
                    {
                        "key": m.key,
                        "title": m.title,
                        "family": m.family,
                        "regime": m.flow_regime,
                        "re_range": (
                            f"{m.validity.get('re_min', '—')}"
                            f"–{m.validity.get('re_max', '—')}"
                        ),
                    }
                    for m in filtered
                ]
                ui.table(columns=columns, rows=rows, row_key="key").classes("w-full")

        family_filter.on("update:model-value", lambda e: render_table(e.args))
        render_table("All")
