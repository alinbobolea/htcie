# htcie Architecture Overview

`htcie` is a transparent, deterministic, API-first correlation decision engine
for single-phase forced-convection heat transfer. The system is built as seven
independent layers, each with a single responsibility and a serializable output.

---

## Seven-Layer Pipeline

```
EngineeringState
       │
       ▼
1. State (htcie.core.state)
       │  Computes Re, Pr, Gz, x/D, S_T/D, S_L/D
       ▼
2. Registry (htcie.core.registry)
       │  Loads correlation metadata from data/correlations/*.yaml
       ▼
3. Applicability (htcie.core.applicability)
       │  Filters by Re/Pr bounds and geometry type; records exclusion reasons
       ▼
4. Evaluation (htcie.core.evaluator → htcie.domains.*)
       │  Computes Nu for each applicable correlation
       ▼
5. Ranking (htcie.core.ranking)
       │  Scores each result with ScoringWeightsV1; returns sorted list
       ▼
6. Confidence / Uncertainty (htcie.core.uncertainty)
       │  Analyses inter-method spread; classifies high/medium/low
       ▼
7. Explanation & Report (htcie.core.explain, htcie.reports)
          Builds human-readable audit trail; serialises to JSON or Markdown
```

The entry point for programmatic use is `htcie.core.pipeline.run_evaluation`,
which chains all seven layers and returns a fully populated `HtcieReport`.

---

## Layer Details

### 1. State — `htcie.core.state`

`EngineeringState` is the single canonical object passed through every layer.
It contains four sub-models (`FluidProperties`, `Geometry`, `BoundaryConditions`,
`FlowState`) and exposes dimensionless groups as Pydantic computed fields:

| Computed field | Formula |
|---|---|
| `reynolds` | $Re = \rho V L / \mu$ |
| `prandtl` | $Pr = c_p \mu / k$ |
| `relative_roughness` | $\varepsilon / D_h$ |
| `graetz` | $Gz = Re \cdot Pr \cdot (D_h / L)$ |
| `entry_length_ratio` | $x/D = L_{dev} / D_h$ |
| `pitch_ratio_transverse` | $S_T / D$ |
| `pitch_ratio_longitudinal` | $S_L / D$ |

### 2. Registry — `htcie.core.registry`

`CorrelationRegistry` loads `*.yaml` files from `data/correlations/` at startup.
Each file describes one correlation: key, family, formula (LaTeX), validity
bounds, assumptions, source reference, and literature uncertainty. The registry
never stores computed values — it is immutable after loading.

### 3. Applicability — `htcie.core.applicability`

`ApplicabilityEngine.evaluate()` checks each correlation's `validity` dict
against the current state in order: geometry type → $Re$ bounds → $Pr$ bounds.
The first failing check produces an explicit exclusion reason. Both the
`applicable` list and `excluded` list (with reasons) are returned.

### 4. Evaluation — `htcie.core.evaluator`

`EvaluationEngine.evaluate()` dispatches to the domain module identified by
the correlation's `family` field. Domain modules (`convection_internal`,
`convection_external`, `tube_banks`) are stateless: they receive the
engineering state and return an `EvaluationResult` containing the computed
Nusselt number and a metadata dict for traceability.

### 5. Ranking — `htcie.core.ranking`

`RankingEngine.rank()` scores each applicable correlation using eight weighted
factors (see [scoring](scoring.rst)). Weights are versioned in
`ScoringWeightsV1`. The returned list is sorted by descending score and each
entry includes a full per-factor breakdown.

### 6. Confidence / Uncertainty — `htcie.core.uncertainty`

Three functions analyse result quality:

- `summarize_spread()` — computes mean, $\sigma$, and relative spread
  ($\sigma / \bar{x}$) across all evaluated Nu values.
- `extrapolation_status()` — measures how far outside its stated validity
  range the best-ranked correlation is operating.
- `confidence_class()` — classifies the result as `"high"`, `"medium"`, or
  `"low"` based on spread and extrapolation ratio.

### 7. Explanation & Report — `htcie.core.explain`, `htcie.reports`

`build_explanation()` constructs a structured `Explanation` object: the
recommended method, score breakdown, exclusion reasons, key assumptions (capped
at three from the correlation's metadata), and a one-sentence recommendation
note.  `Explanation.to_text()` renders the same data as a human-readable
multi-line string; this rendered text is also included as the `"text"` key
when the explanation is serialised via `to_dict()`.

`HtcieReport` packages the complete audit trail into a single Pydantic model.
`to_dict()` produces a JSON-serialisable dict — this is also the payload
returned directly by `POST /evaluate`.  Three serialisation helpers write the
report to disk:

| Function | Module | Output |
|---|---|---|
| `dump_json_report()` | `htcie.reports.serializers` | Machine-readable JSON |
| `dump_markdown_report()` | `htcie.reports.serializers` | Human-readable Markdown |
| `dump_html_report()` | `htcie.reports.serializers` | Self-contained HTML (via Jinja2), no charts |

`render_html()` in `htcie.reports.renderer` returns the HTML string directly
and accepts an optional `charts` dict of pre-rendered Plotly fragments
(`"ranking"` and `"uncertainty"` keys).  `dump_html_report` / `save_html`
do not forward charts — call `render_html` directly when chart embedding is
needed.

---

## Design Principles

- **Deterministic** — All scoring and filtering use explicit, auditable logic.
  No machine learning, no stochastic tie-breaking.
- **Metadata-driven** — Correlations are defined in YAML, not in Python code,
  so adding a new correlation requires no code changes to the engine.
- **Explanation-first** — Every result includes a full audit trail. Exclusion
  reasons, score breakdowns, and extrapolation warnings are first-class outputs.
- **Versioned scoring** — `ScoringWeightsV1` enables future scoring policy
  changes while preserving reproducibility of past reports.
- **API-first** — The CLI and GUI are clients of the same core pipeline used by
  the REST API. There is no separate code path per interface.
- **No hidden state** — All singletons (registry, engines) are explicit. No
  module-level caches mutate between requests.
