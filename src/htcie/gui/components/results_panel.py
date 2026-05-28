"""Results display component."""

from __future__ import annotations

from nicegui import ui

from htcie.gui.components.charts import render_ranking_chart, render_uncertainty_chart


CONFIDENCE_COLORS = {
    "high": "positive",
    "medium": "warning",
    "low": "negative",
}


def _build_explanation_md(explanation: dict) -> str:
    """Build a Markdown string from the structured explanation dict."""
    lines: list[str] = []

    best_method = explanation.get("best_method", "")
    if best_method:
        lines += [f"Scoring rationale for **`{best_method}`**", ""]

    breakdown = explanation.get("score_breakdown", {})
    if breakdown:
        lines += ["**Score Breakdown**", ""]
        lines += ["| Factor | Score |", "| --- | --- |"]
        for factor, value in breakdown.items():
            lines.append(f"| {factor} | {value:.3f} |")
        lines.append("")

    assumptions = explanation.get("key_assumptions", [])
    if assumptions:
        lines += ["**Key Assumptions**", ""]
        for a in assumptions:
            lines.append(f"- {a}")
        lines.append("")

    warnings = explanation.get("extrapolation_warnings", [])
    if warnings:
        lines += ["**Extrapolation Warnings**", ""]
        for w in warnings:
            lines.append(f"- ⚠ {w}")
        lines.append("")

    rec = explanation.get("recommendation_note", "")
    if rec:
        lines.append(f"*{rec}*")

    return "\n".join(lines)


def render_results(result: dict) -> None:
    """Render evaluation results in the current NiceGUI context."""
    if "error" in result:
        ui.label(result["error"]).classes("text-red-500")
        return

    confidence = result.get("confidence", "low")
    badge_color = CONFIDENCE_COLORS.get(confidence, "grey")

    explanation = result.get("explanation", {})
    best_method = explanation.get("best_method", "—")
    best_score = explanation.get("best_score", 0.0)

    evaluations = result.get("evaluations", [])
    best_eval = next((e for e in evaluations if e["key"] == best_method), None)

    def _fmt_derived(v: float) -> str:
        if abs(v) >= 1000:
            return f"{v:,.0f}"
        if abs(v) >= 1:
            return f"{v:.4g}"
        return f"{v:.3e}"

    _DERIVED_SHORT = {
        "reynolds": "Re",
        "prandtl": "Pr",
        "graetz": "Gz",
        "entry_length_ratio": "L/D",
        "relative_roughness": "ε/D",
        "pitch_ratio_transverse": "S\u1d40/D",
        "pitch_ratio_longitudinal": "S\u1d38/D",
    }
    derived = result.get("derived", {})
    derived_parts = [
        f"<b>{_DERIVED_SHORT.get(k, k)}</b> = {_fmt_derived(v)}"
        for k, v in derived.items()
        if v is not None
    ]

    with ui.card().classes("w-full"):
        with ui.row():
            ui.label(f"Recommended Heat Transfer Correlation: {best_method}").classes(
                "text-lg font-semibold"
            )
            ui.badge(confidence.capitalize(), color=badge_color)
        if best_eval:
            h = best_eval.get("h")
            h_low = best_eval.get("h_low")
            h_high = best_eval.get("h_high")
            if h is not None:
                if h_low is not None and h_high is not None:
                    ui.html(
                        f"<b>h = {h:.1f} W/m²·K"
                        f" &nbsp; [{h_low:.1f}, {h_high:.1f}] W/m²·K</b>"
                    )
                else:
                    ui.html(f"<b>h = {h:.1f} W/m²·K</b>")
        ui.html(f"<b>Score: {best_score:.3f}</b>")
        if derived_parts:
            ui.html(" &nbsp;·&nbsp; ".join(derived_parts))

    # Ranking score chart (Plotly)
    ranking = result.get("ranking", [])
    if ranking:
        ui.label("Correlation Ranking Score").classes("text-lg font-semibold mt-2")
        render_ranking_chart(ranking)

    # Uncertainty band chart (Plotly)
    if evaluations and ranking:
        ui.label("Heat Transfer Coefficient with Uncertainty").classes(
            "text-lg font-semibold mt-2"
        )
        render_uncertainty_chart(evaluations, ranking)

    # Explanation
    if explanation.get("best_method"):
        with (
            ui.expansion("Explanation", icon="insights")
            .classes("w-full")
            .props('header-class="font-bold"')
        ):
            ui.markdown(_build_explanation_md(explanation)).classes("w-full")

    # Excluded methods
    excluded = result.get("excluded", [])
    if excluded:
        with (
            ui.expansion(
                f"Excluded Methods ({len(excluded)})", icon="do_not_disturb_on"
            )
            .classes("w-full")
            .props('header-class="font-bold"')
        ):
            lines = ["| Correlation | Reason |", "| --- | --- |"]
            for item in excluded:
                lines.append(f"| `{item['key']}` | {item['reason']} |")
            ui.markdown("\n".join(lines)).classes("w-full")
