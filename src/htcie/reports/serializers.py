"""Serialization helpers for writing an :class:`~htcie.reports.schema.HtcieReport` to disk.

Three formats are supported:

- :func:`dump_json_report` — JSON (machine-readable, fully self-contained)
- :func:`dump_markdown_report` — Markdown (human-readable summary)
- :func:`dump_html_report` — self-contained HTML (via Jinja2 template)

All three formats are derived from
:meth:`~htcie.reports.schema.HtcieReport.to_dict`.  The :func:`to_dict`
function is provided as a convenience alias for callers that want the dict
without writing a file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from htcie.reports.schema import HtcieReport


def dump_json_report(report: dict[str, Any] | HtcieReport, path: str | Path) -> None:
    """Write *report* as indented JSON to *path*.

    Accepts either an :class:`~htcie.reports.schema.HtcieReport` (converted via
    :meth:`~htcie.reports.schema.HtcieReport.to_dict`) or a plain dict (written
    as-is).  The plain-dict path is useful when the caller has already called
    ``to_dict()`` and wants to add or strip fields before writing.

    Args:
        report: Report object or pre-serialised dict.
        path: Destination file path.  Parent directory must exist.
    """
    path = Path(path)
    if isinstance(report, HtcieReport):
        data = report.to_dict()
    else:
        data = report
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def dump_html_report(report: HtcieReport, path: str | Path) -> None:
    """Render *report* as self-contained HTML and write it to *path*.

    Delegates to :func:`~htcie.reports.renderer.save_html`.  The renderer is
    imported lazily to avoid a circular import between the serializers and
    renderer modules.

    Args:
        report: A fully populated :class:`~htcie.reports.schema.HtcieReport`.
        path: Destination file path.  Parent directory must exist.
    """
    from htcie.reports.renderer import save_html  # local import avoids circular

    save_html(report, path)


def dump_markdown_report(report: HtcieReport, path: str | Path) -> None:
    """Render *report* as Markdown and write it to *path*.

    Args:
        report: A fully populated :class:`~htcie.reports.schema.HtcieReport`.
        path: Destination file path.  Parent directory must exist.
    """
    path = Path(path)
    path.write_text(_render_markdown(report), encoding="utf-8")


def to_dict(report: HtcieReport) -> dict[str, Any]:
    """Return the JSON-serialisable dict for *report*.

    Thin alias for :meth:`~htcie.reports.schema.HtcieReport.to_dict` provided
    so callers can use a consistent functional style (``to_dict(report)``)
    alongside the three ``dump_*`` helpers without holding a method reference.
    """
    return report.to_dict()


def _render_markdown(report: HtcieReport) -> str:
    """Render *report* as a Markdown string.

    Sections (in order): header metadata, recommended method (via
    :meth:`~htcie.core.explain.Explanation.to_text`), applicable methods,
    excluded methods (or "*(none)*" if all passed), evaluation results table
    (method and Nu only), spread summary table, and input conditions table.

    The ``graetz`` row in the input conditions table is omitted when the value
    is ``None`` (i.e. for external-flow geometries).

    Returns:
        Multi-line Markdown string ready to write to a ``.md`` file.
    """
    lines = [
        "# htcie Evaluation Report",
        "",
        f"**Engine version:** {report.engine_version}  ",
        f"**Timestamp:** {report.timestamp}  ",
        f"**Confidence:** {report.confidence}  ",
        "",
        "## Recommended Method",
        "",
        "```",
        report.explanation.to_text(),
        "```",
        "",
        "## Applicable Methods",
        "",
    ]
    for key in report.applicable:
        lines.append(f"- `{key}`")
    lines.extend(
        [
            "",
            "## Excluded Methods",
            "",
        ]
    )
    if report.excluded:
        for item in report.excluded:
            lines.append(f"- `{item['key']}`: {item['reason']}")
    else:
        lines.append("*(none)*")
    lines.extend(
        [
            "",
            "## Evaluation Results",
            "",
            "| Method | Nu |",
            "|--------|-----|",
        ]
    )
    for ev in report.evaluations:
        lines.append(f"| `{ev['key']}` | {ev['value']:.4f} |")
    lines.extend(
        [
            "",
            "## Spread Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Count | {report.spread.get('count', 'N/A')} |",
            (
                f"| Mean Nu | {report.spread.get('mean', 'N/A'):.4f} |"
                if report.spread.get("mean")
                else "| Mean Nu | N/A |"
            ),
            (
                f"| Std Dev | {report.spread.get('stdev', 'N/A'):.4f} |"
                if report.spread.get("stdev") is not None
                else "| Std Dev | N/A |"
            ),
            (
                f"| Relative Spread | {report.spread.get('relative_spread', 0):.2%} |"
                if report.spread.get("relative_spread") is not None
                else "| Relative Spread | N/A |"
            ),
            "",
            "## Input State",
            "",
            "| Parameter | Value |",
            "|-----------|-------|",
            f"| Geometry type | {report.input_state.geometry.geometry_type} |",
            (
                f"| Re | {report.derived.get('reynolds', 'N/A'):.1f} |"
                if report.derived.get("reynolds")
                else "| Re | N/A |"
            ),
            (
                f"| Pr | {report.derived.get('prandtl', 'N/A'):.3f} |"
                if report.derived.get("prandtl")
                else "| Pr | N/A |"
            ),
        ]
    )
    if report.derived.get("graetz") is not None:
        lines.append(f"| Gz | {report.derived['graetz']:.2f} |")
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated by htcie v{report.engine_version}*")
    return "\n".join(lines)
