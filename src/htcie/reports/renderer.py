"""Jinja2-based HTML renderer for :class:`~htcie.reports.schema.HtcieReport`.

A single Jinja2 :class:`~jinja2.Environment` (``_ENV``) is created once at
module import time and reused for all render calls.  The environment loads the
``report.html.j2`` template from the ``templates/`` directory co-located with
this module and enables auto-escaping for HTML files.

The template receives the output of
:meth:`~htcie.reports.schema.HtcieReport.to_dict` — a plain dict — not the
``HtcieReport`` object itself.  This keeps the template decoupled from the
Pydantic model and ensures the rendered output matches exactly what
``dump_json_report`` would write.
"""

from __future__ import annotations

from pathlib import Path

import jinja2

from htcie.reports.schema import HtcieReport

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=jinja2.select_autoescape(["html"]),
)


def render_html(
    report: HtcieReport,
    charts: dict[str, str] | None = None,
) -> str:
    """Render *report* as a self-contained HTML string.

    Calls :meth:`~htcie.reports.schema.HtcieReport.to_dict` and passes the
    resulting plain dict to the ``report.html.j2`` Jinja2 template.  The
    output includes inline CSS and no external dependencies.

    Args:
        report: A fully populated HtcieReport.
        charts: Optional dict of pre-rendered Plotly HTML fragments keyed by
            ``"ranking"`` and ``"uncertainty"``.  When provided, the charts
            are embedded in the report.  Omit (or pass ``None``) for
            chart-free output suitable for programmatic use.

    Returns:
        UTF-8 HTML string suitable for writing to a ``.html`` file.
    """
    template = _ENV.get_template("report.html.j2")
    return template.render(report=report.to_dict(), charts=charts)


def save_html(report: HtcieReport, path: str | Path) -> None:
    """Render *report* as HTML and write it to *path*.

    Charts are not embedded — the output is equivalent to calling
    ``render_html(report, charts=None)``.  To embed Plotly charts, call
    :func:`render_html` directly with a ``charts`` dict and write the
    returned string yourself.

    Args:
        report: A fully populated HtcieReport.
        path: Destination file path. Parent directory must exist.
    """
    Path(path).write_text(render_html(report), encoding="utf-8")
