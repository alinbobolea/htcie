# Development Log

## 2026-03-28 — Pre-launch audit: 23 issues fixed (5C / 7H / 7M / 4L)

Complete pre-launch audit across scientific correctness, code quality, testing, data
integrity, and production readiness. All identified issues resolved.

**Critical fixes:**
- **C1 Gnielinski off-by-one**: `if re <= 3000` → `if re < 3000` — Re=3000 previously
  passed applicability but crashed the evaluator.
- **C2 Churchill-Bernstein lower bound**: Added explicit YAML assumption surfacing that
  this formula is a lower bound per the original paper (CB 1977, p. 304).
- **C3 Re gap 2300–3000 diagnostics**: API router now returns excluded-correlation list
  instead of a generic "no methods" string when no correlations are applicable.
- **C4 Petukhov uncertainty corrected**: `literature_uncertainty_pct` raised 6% → 10%
  (primary source states ±10% for full Pr 0.5–2000 range).
- **C5 Film temperature advisory**: Pipeline now emits `warnings` list when external
  geometry is used without `wall_temperature` provided.

**High fixes:**
- **H1/H3 Table upper-bound crashes**: Hilpert Re=400,000 and Žukauskas Re=1,000,000
  previously fell through all table bands and raised ValueError. Fixed by using `<=`
  on table upper bounds.
- **H2 Negative Nu guard**: Turbulent plate now raises ValueError for Re < 5×10⁵
  instead of returning negative Nu.
- **H4 Score clamping**: `RankingEngine._score()` now clamps result to [0.0, 1.0].
- **H5 Dead code removed**: Three unused engine singletons removed from `api/dependencies.py`.
- **H6 Petukhov test**: Added `TestPetukhov` with formula accuracy and comparison tests.
- **H7 ld_min validation**: Applicability engine now enforces `ld_min` from YAML validity
  dicts (using existing `entry_length_ratio` computed field).

**Medium/Low fixes:**
- **M2**: `_require_re_pr` extracted to `src/htcie/domains/_helpers.py`; all three domain
  modules import from shared location.
- **M3**: Score-range test extended to Re=1e9 (extreme extrapolation path).
- **M4**: Report timestamp uses `datetime.now(timezone.utc)` (was naive local time).
- **M6**: `wall_prandtl_note` metadata key added when wall-Prandtl correction is applied.
- **L4**: Gnielinski test updated to reflect inclusive Re=3000 boundary.

## 2026-03-28 — Primary-source traceability audit (all 13 correlations)

Systematic audit of every `literature_uncertainty_pct` and key validity range against
primary sources and authoritative textbooks. Four substantive corrections; all 13
correlations now carry explicit source-traceability notes.

**Substantive corrections:**

1. **Žukauskas tube bank `re_min` (10 → 20)**: Primary source p.147 (Advances in Heat
   Transfer Vol. 8, 1972) explicitly states the validated-data summary covers "Re from
   20 to 2×10^6". YAML had `re_min: 10`; Incropera references.yaml noted 16; primary
   source is authoritative at 20. Three-source discrepancy documented in YAML notes.

2. **Petukhov accuracy range (split by Pr)**: Primary source p.523 Eq.(50) states ±5–6%
   for Re 10^4–5×10^6 and **Pr 0.5–200** separately from ±10% for **Pr 0.5–2000**. YAML
   note previously claimed ±6% uniformly for Pr up to 2000 — incorrect. Fixed with exact
   page citation.

3. **Churchill-Bernstein lower-bound characterization**: Original paper (p.304) explicitly
   states Eq.(9) "is proposed as a lower bound...data generally fall somewhat above." No
   ±% is stated anywhere in the paper. YAML previously said "±20% reported in original
   paper" — corrected to lower-bound characterization with page citation.

4. **Gnielinski ±10% attribution**: The ±10% comes from Cengel & Ghajar 5th ed.
   (Section 8-5), not the 1976 original paper (inaccessible) or the available 2013 update
   (IJHMT 63:134-140, which does not restate this value). Attribution corrected.

**Systematic UNCERTAIN flagging:** All 13 `literature_uncertainty_pct` values annotated.
Only Petukhov's ±5–6%/±10% is directly confirmed from a primary source. All others are
textbook-consensus estimates; each carries an explicit `UNCERTAIN` note explaining why the
primary source could not confirm the stated bound (paywall, no ±% in paper, analytical
solution only, or no single original paper).

**Sources inspected:** Žukauskas (1972), "Heat Transfer from Tubes in Crossflow," *Advances in Heat Transfer*, Vol. 8 (pp. 142–157);
Gnielinski (2013), "On heat transfer in tubes," *Int. J. Heat Mass Transfer*, 63:134–140;
Churchill & Bernstein (1977), "A Correlating Equation for Forced Convection from Gases and Liquids to a Circular Cylinder in Crossflow," *J. Heat Transfer (ASME)*, 99(2):300–306;
Petukhov (1970), "Heat Transfer and Friction in Turbulent Pipe Flow with Variable Physical Properties," *Advances in Heat Transfer*, Vol. 6, pp. 503–564 (p. 523);
Sieder & Tate (1936), "Heat Transfer and Pressure Drop of Liquids in Tubes," *Ind. Eng. Chem.*, 28(12):1429–1435 (Table II).

## 2026-03-27 — Explicit tube bank arrangement field

Added `arrangement: Optional[Literal["inline", "staggered"]]` to `Geometry` in
`state.py`, required when `geometry_type="tube_bank"`. Previously the arrangement
was inferred from S_T/S_L < 1.0, which made the Incropera Table 7.5 staggered
S_T/S_L ≥ 2 case (C₁=0.40) permanently unreachable.

Changes: `state.py` (new field + validator), `tube_banks.py` (removed `_arrangement()`
helper, added `_require_arrangement()` reading from state), YAML `required_inputs`
for both tube bank correlations, 3 test files updated.

## 2026-03-27 — Validation-grade correlation audit (Incropera 7th ed.)

Verified all 13 correlations against Incropera 7th edition (primary reference) and
original papers. Corrected four substantive errors:

1. **Žukauskas cylinder Pr exponent** (`external.zukauskas_cylinder`): Fixed from
   hardcoded `n=0.36` to `n=0.37` for Pr ≤ 10, `n=0.36` for Pr > 10 per Incropera
   Eq 7.53. This matters for gases (Pr ≈ 0.7), where the previous value was wrong.

2. **Žukauskas tube bank coefficients** (`tube_banks.zukauskas`): Corrected all Re
   bands against Incropera Table 7.5:
   - Re < 100: inline 0.9→0.80, staggered 1.04→0.90
   - Re 100–1000: raised `ValueError` (Incropera says approximate as single cylinder;
     previous values 0.52/0.71 were unsourced)
   - Re > 2×10^5: inline 0.033/0.8→0.021/0.84, staggered 0.031·…/0.8→0.022/0.84
   - Added staggered S_T/S_L ≥ 2 case (C=0.40) — currently dead code pending explicit
     arrangement field in state schema (see TODO in tube_banks.py)

3. **Dittus-Boelter Pr lower bound**: corrected `pr_min` from 0.7 to 0.6 per Incropera
   Eq 8.60. The `re_max=120000` bound is retained (McAdams 1954).

4. **Sieder-Tate Pr upper bound**: corrected `pr_max` from 17000 to 16700 per Incropera
   Eq 8.61.

All other correlations (Churchill-Bernstein, Hilpert, Pohlhausen, turbulent plate,
Gnielinski, Petukhov, Shah laminar, Churchill-Ozoe, Grimison) verified correct.

Updated 4 YAML files, 2 domain source files, 2 test files. 167 tests pass.

## 2026-03-26 — HTML report renderer
- Added `src/htcie/reports/renderer.py` with `render_html` / `save_html` public API.
- Added `src/htcie/reports/templates/report.html.j2` — self-contained Jinja2 template
  covering all report sections (input conditions, dimensionless groups, evaluations,
  ranking, spread, explanation).
- Exposed `render_html`, `save_html`, `dump_html_report` from `htcie.reports` package.
- Added "Save as HTML" button to htcie-gui evaluate page (disabled until evaluation runs).
- Added demonstration cell to `notebooks/examples.ipynb` under "Using the Report Downstream".
- Extracted shared test fixtures to `tests/unit/conftest.py`; added 7 renderer tests.

## 2026-03-25 — Code quality and docstring pass
- Added class and method docstrings throughout `src/htcie/`.
- All formula-containing docstrings use LaTeX (`:math:` RST role).
- Updated `docs/architecture/overview.md` with full pipeline diagram and
  layer-by-layer detail.
- Updated `docs/architecture/scoring.rst` with correct v1 factor names,
  weights table, and threshold reference.
- Updated `docs/methods/metadata-schema.md` to reflect all implemented fields
  (removed stale "planned" notes).
- Updated correlation docs (`internal.rst`, `external.rst`, `tube_banks.rst`)
  with formula descriptions and implementation notes.

## Initial scaffold
- Renamed starter kit to `htcie` and regenerated the full repository scaffold.
- Implemented seven-layer pipeline: state → registry → applicability →
  evaluation → ranking → confidence → explanation/report.
- Implemented 13 correlations across three domain families:
  6 internal convection, 5 external convection, 2 tube banks.
- Implemented Scoring v1 with eight weighted factors.
- Added FastAPI REST API, Typer CLI, and NiceGUI web interface.
- Added JSON and Markdown report serializers.
