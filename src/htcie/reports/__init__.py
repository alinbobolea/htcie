"""Report serialization and rendering for htcie evaluation results.

This package provides three output formats for an :class:`~htcie.reports.schema.HtcieReport`:

- **JSON** — ``dump_json_report(report, path)`` writes a fully self-contained,
  machine-readable audit record. Useful for downstream tooling, storage, and
  diff-based auditing.
- **Markdown** — ``dump_markdown_report(report, path)`` writes a human-readable
  report covering the recommendation, applicable/excluded methods, evaluation
  table, spread summary, and input conditions.
- **HTML** — ``dump_html_report(report, path)`` writes a self-contained HTML
  file with inline CSS. Suitable for sharing or archiving without external
  dependencies.

All three formats are derived from :meth:`~htcie.reports.schema.HtcieReport.to_dict`,
which produces the canonical JSON-serialisable representation of the report.

``to_dict(report)`` is also exported directly from this package as a functional
alias for callers who prefer a consistent ``dump_*`` / ``to_dict`` style without
holding a method reference.
"""

from htcie.reports.renderer import render_html, save_html
from htcie.reports.schema import HtcieReport
from htcie.reports.serializers import (
    dump_html_report,
    dump_json_report,
    dump_markdown_report,
    to_dict,
)

__all__ = [
    "HtcieReport",
    "render_html",
    "save_html",
    "dump_html_report",
    "dump_json_report",
    "dump_markdown_report",
    "to_dict",
]
