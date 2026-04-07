"""Tests for reports schema and serializers."""

from __future__ import annotations

import json

from htcie.reports.schema import HtcieReport
from htcie.reports.serializers import (
    dump_html_report,
    dump_json_report,
    dump_markdown_report,
    to_dict,
)


def test_report_to_dict_is_json_serializable(sample_report: HtcieReport) -> None:
    d = sample_report.to_dict()
    json.dumps(d)


def test_report_to_dict_has_required_keys(sample_report: HtcieReport) -> None:
    d = sample_report.to_dict()
    for key in [
        "engine_version",
        "timestamp",
        "applicable",
        "excluded",
        "evaluations",
        "ranking",
        "spread",
        "confidence",
        "explanation",
        "scoring_weights_version",
    ]:
        assert key in d, f"Missing key: {key}"


def test_report_explanation_in_dict(sample_report: HtcieReport) -> None:
    d = sample_report.to_dict()
    assert "text" in d["explanation"]
    assert "best_method" in d["explanation"]


def test_dump_json_report(sample_report: HtcieReport, tmp_path: object) -> None:
    out = tmp_path / "report.json"  # type: ignore[operator]
    dump_json_report(sample_report, out)
    data = json.loads(out.read_text())
    assert data["confidence"] == "high"


def test_dump_markdown_report(sample_report: HtcieReport, tmp_path: object) -> None:
    out = tmp_path / "report.md"  # type: ignore[operator]
    dump_markdown_report(sample_report, out)
    content = out.read_text()
    assert "# htcie Evaluation Report" in content
    assert "internal.gnielinski" in content


def test_dump_html_report(sample_report: HtcieReport, tmp_path: object) -> None:
    out = tmp_path / "report.html"  # type: ignore[operator]
    dump_html_report(sample_report, out)
    content = out.read_text()  # type: ignore[union-attr]
    assert "<!DOCTYPE html>" in content
    assert "internal.gnielinski" in content


def test_to_dict_function(sample_report: HtcieReport) -> None:
    d = to_dict(sample_report)
    assert d["scoring_weights_version"] == "v1"
