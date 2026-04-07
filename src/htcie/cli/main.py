"""CLI entry point for htcie."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from htcie.core.loader import build_registry
from htcie.core.pipeline import run_evaluation
from htcie.core.registry import CorrelationRegistry
from htcie.core.state import EngineeringState
from htcie.reports.serializers import dump_json_report, dump_markdown_report

console = Console()

app = typer.Typer(help="htcie — Heat Transfer Correlation Intelligence Engine")
methods_app = typer.Typer(help="Browse correlation methods")
app.add_typer(methods_app, name="methods")


def _load_registry() -> CorrelationRegistry:
    """Load and return a :class:`~htcie.core.registry.CorrelationRegistry`."""
    return build_registry()


@app.command()
def evaluate(
    input_json: Path = typer.Argument(
        ..., help="Path to JSON file with EngineeringState"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Save report to file"
    ),
    markdown: bool = typer.Option(False, "--markdown", "-m", help="Output as Markdown"),
) -> None:
    """Run evaluation pipeline for an engineering state."""
    data = json.loads(input_json.read_text(encoding="utf-8"))
    state = EngineeringState.model_validate(data)
    registry = _load_registry()

    report = run_evaluation(state, registry)
    if report is None:
        rprint("[yellow]No applicable methods found for the given state.[/yellow]")
        raise typer.Exit(code=1)

    if output:
        if markdown:
            dump_markdown_report(report, output)
            console.print(f"[green]Report saved to {output}[/green]")
        else:
            dump_json_report(report, output)
            console.print(f"[green]Report saved to {output}[/green]")
    elif markdown:
        from htcie.reports.serializers import _render_markdown

        console.print(_render_markdown(report))
    else:
        rprint(report.to_dict())


@methods_app.command("list")
def methods_list(
    family: Optional[str] = typer.Option(
        None, "--family", "-f", help="Filter by family"
    ),
) -> None:
    """List all available correlation methods."""
    registry = _load_registry()
    if family:
        items = registry.by_family(family)
    else:
        items = registry.all()

    if not items:
        console.print("[yellow]No correlations found.[/yellow]")
        return

    table = Table(title="htcie Correlation Methods")
    table.add_column("Key", style="cyan")
    table.add_column("Title")
    table.add_column("Family")
    table.add_column("Re range")
    table.add_column("Regime")

    for m in sorted(items, key=lambda x: x.key):
        re_min = m.validity.get("re_min", "—")
        re_max = m.validity.get("re_max", "—")
        re_range = f"{re_min}–{re_max}" if re_min != "—" or re_max != "—" else "—"
        table.add_row(m.key, m.title, m.family, re_range, m.flow_regime)

    console.print(table)


@methods_app.command("show")
def methods_show(
    key: str = typer.Argument(..., help="Correlation key (e.g. internal.gnielinski)"),
) -> None:
    """Show full metadata for one correlation."""
    registry = _load_registry()
    try:
        meta = registry.get(key)
    except KeyError:
        console.print(f"[red]Method '{key}' not found.[/red]")
        raise typer.Exit(code=1)

    rprint(meta.model_dump())


@app.command()
def gui() -> None:
    """Launch the htcie NiceGUI web interface."""
    try:
        from htcie.gui.main import run

        run()
    except ImportError:
        console.print(
            "[yellow]NiceGUI GUI not available. Install with: uv add nicegui[/yellow]"
        )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
