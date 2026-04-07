# htcie — Heat Transfer Correlation Intelligence Engine

**Transparent, deterministic, API-first correlation decision engine for single-phase convection heat transfer.**

![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)
![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)

---

## What is htcie?

`htcie` is a lightweight, open-source correlation decision engine for single-phase convection heat transfer. It accepts engineering inputs — geometry, fluid properties, flow conditions, and boundary conditions — and runs a full, auditable decision pipeline: it identifies every applicable correlation, evaluates them numerically, ranks them with a deterministic scoring model, and reports confidence based on inter-method spread.

The product answers five engineering questions directly:

1. Which methods are valid for my conditions?
2. What Nu or h does each valid method predict?
3. Which method is recommended, and why?
4. How much do the candidate methods disagree?
5. How confident should I be in the result?

---

## Quick Install

```bash
pip install htcie
# or with uv
uv add htcie
```

A hosted instance is also available — the API at `https://htcie-api.onrender.com` and the GUI at `https://htcie-gui.onrender.com` run on Render.com's free tier (expect a ~30 s cold-start if the service has been idle). See [DEPLOY.md](DEPLOY.md) to self-host your own instance.

---

## Quickstart

**Python API**

```python
from htcie.core.pipeline import run_evaluation
from htcie.core.registry import CorrelationRegistry
from htcie.core.state import (
    EngineeringState, FluidProperties, Geometry,
    BoundaryConditions, FlowState,
)

state = EngineeringState(
    fluid=FluidProperties(
        density=998.2,
        viscosity=1.002e-3,
        thermal_conductivity=0.598,
        heat_capacity=4182,
    ),
    geometry=Geometry(
        geometry_type="circular_tube",
        characteristic_length=0.025,
        hydraulic_diameter=0.025,
    ),
    boundary=BoundaryConditions(boundary_type="constant_wall_temperature"),
    flow=FlowState(velocity=0.4),
)

registry = CorrelationRegistry()
registry.load_from_dir("data/correlations")

report = run_evaluation(state, registry)
if report:
    print(report.explanation.to_text())  # human-readable recommendation
    print(report.confidence)             # "high", "medium", or "low"
```

**CLI**

```bash
htcie evaluate input.json
htcie evaluate input.json --output report.md --markdown
```

**GUI**

```bash
htcie gui
```

---

## Notebooks

Three JupyterLab notebooks are available in the [`notebooks/`](notebooks/) directory. Clone the repo and run `uv run jupyter lab` to open them.

| Notebook | What it shows |
|---|---|
| [`examples.ipynb`](notebooks/examples.ipynb) | Step-by-step walkthrough of all 7 pipeline stages — applicability, evaluation, uncertainty bands, ranking, confidence, explanation, and report serialisation |
| [`gtm_demo.ipynb`](notebooks/gtm_demo.ipynb) | Narrative demo comparing manual Dittus-Boelter lookup against the full htcie workflow — covers all four differentiators with interactive charts |
| [`benchmark.ipynb`](notebooks/benchmark.ipynb) | Validates all 13 correlations against Incropera 7th ed. reference values across 5 test cases (14/14 pass) |

---

## Architecture

`htcie` processes every request through a seven-layer pipeline:

```
Engineering State
      |
Correlation Registry
      |
Applicability Engine   — filters methods; records exclusion reasons
      |
Evaluation Engine      — computes Nu/h for each applicable method
      |
Ranking Engine         — deterministic score: validity fit + pedigree + geometry match
      |
Confidence Engine      — spread, confidence class (High / Medium / Low)
      |
Explanation Layer      — why this method was chosen and what was excluded
```

Each layer is independently testable and the full result is packaged into an `HtcieReport` — a self-contained Pydantic model holding inputs, derived dimensionless groups, all candidate outputs with uncertainty bands, ranking breakdown, confidence class, and a structured explanation. Reports can be serialised to JSON, Markdown, or self-contained HTML.

---

## Correlation Catalog

13 MVP correlations across three families. All entries carry source metadata, validity rules, assumptions, and notes.

### Internal Forced Convection — Circular Tubes

| Key | Authors | Year | Re Range | Notes |
|---|---|---|---|---|
| `dittus_boelter` | Dittus, Boelter | 1930 | 10 000 – 120 000 | Classic turbulent; ±25%; simple but coarse |
| `sieder_tate` | Sieder, Tate | 1936 | 10 000 – 1 000 000 | Viscosity-corrected; preferred for high-viscosity fluids |
| `gnielinski` | Gnielinski | 1976 | 3 000 – 5 000 000 | Preferred default; extends Petukhov to Re = 3 000; ±10% |
| `petukhov` | Petukhov | 1970 | 10 000 – 5 000 000 | Friction-factor-based; ±6%; basis for Gnielinski |
| `shah_laminar` | Shah | 1978 | Re < 2 300 | Thermally developing laminar (UWT); Graetz entry-length |
| `churchill_ozoe_laminar` | Churchill, Ozoe | 1973 | Re < 2 300 | Laminar developing; supports both UWT and UHF |

### External Forced Convection

| Key | Authors | Year | Re Range | Notes |
|---|---|---|---|---|
| `churchill_bernstein_cylinder` | Churchill, Bernstein | 1977 | 0 – 4 × 10^7 | Preferred all-Re cylinder correlation; ±20% |
| `hilpert_cylinder` | Hilpert | 1933 | 0.4 – 400 000 | Classic tabular C/m; gases; superseded by Churchill-Bernstein |
| `zukauskas_cylinder` | Žukauskas | 1972 | 1 – 1 000 000 | Wall-Pr correction; covers gases and liquids |
| `pohlhausen_plate_laminar` | Pohlhausen | 1921 | Re_L < 500 000 | Laminar flat plate (Blasius); ±10% |
| `turbulent_plate` | Incropera, DeWitt | 2007 | 500 000 – 10 000 000 | Mixed laminar-turbulent flat plate; transition at Re = 5 × 10^5 |

### Tube Banks

| Key | Authors | Year | Re Range | Notes |
|---|---|---|---|---|
| `zukauskas_bank` | Žukauskas | 1972 | 16 – 2 000 000 | Inline and staggered; row correction; wall-Pr correction |
| `grimison_bank` | Grimison | 1937 | 2 000 – 40 000 | Older tabular correlation; superseded by Žukauskas for wider Re |

---

## Validation and Uncertainty

All 13 correlations have been systematically reviewed against Incropera *Fundamentals of Heat and Mass Transfer* (7th ed.) and, where accessible, against original primary sources. Each correlation entry in the [correlation catalog](docs/correlations/) records: equation source, validity bounds (Re, Pr, geometry), assumptions, and explicit uncertainty notes.

**What was verified:**

- All formula coefficients, exponents, and tabular constants were checked against Incropera 7th ed. (the primary textbook reference) and corrected where discrepancies were found.
- Four substantive formula errors were corrected during the validation process (Žukauskas Pr exponent, tube-bank coefficients, Dittus-Boelter Pr lower bound, Sieder-Tate Pr upper bound).
- Five primary-source PDFs were reviewed in full (Žukauskas 1972, Gnielinski 2013 update, Churchill-Bernstein 1977, Petukhov 1970, Sieder-Tate 1936).

**Uncertainty bounds — honest state:**

The literature uncertainty percentages reported by the engine (used in scoring and confidence bands) carry the following caveats, documented in detail in the [correlation catalog](docs/correlations/):

- **Petukhov (±5–6% for Pr 0.5–200; ±10% for Pr 0.5–2,000)** is the *only* uncertainty bound verified directly from an accessible primary source (Petukhov 1970, p. 523).
- All other uncertainty figures — including Gnielinski ±10%, Dittus-Boelter ±25%, Churchill-Bernstein ±20%, Žukauskas ±25%, Sieder-Tate ±20%, and the laminar correlations at ±10% — are **textbook-consensus estimates**. The original papers were either paywalled, unavailable in any accessible digital form, or (in the case of Churchill-Bernstein) simply did not state an explicit ±% bound. These are marked `UNCERTAIN` in the catalog with the reason.
- **Churchill-Bernstein** is not a central estimate: the original paper (CB 1977, p. 304) explicitly characterises Eq. (9) as "a lower bound for computed and experimental values." Actual Nusselt numbers typically fall *above* this correlation. The engine surfaces this as an assumption in the explanation layer.
- **Sieder-Tate**: inspection of the original paper (Table II, p. 1433) shows deviations ranging from ±4% to ±63% by fluid type and Re regime. The commonly cited ±20% is a textbook simplification.

These limitations do not prevent the engine from being useful: the ranking engine applies the stated uncertainty values as *relative* weights, so correlations with lower stated uncertainty (e.g. Gnielinski) score above those with higher uncertainty (e.g. Dittus-Boelter) when both are applicable — regardless of whether the absolute bound was verified from a primary source. The confidence class reported in each result reflects inter-method spread, not the absolute accuracy of any single correlation.

For full traceability details, per-correlation source citations, and the complete list of `UNCERTAIN` flags, see the [Internal Convection catalog](docs/correlations/internal.rst), [External Convection catalog](docs/correlations/external.rst), and [Tube Banks catalog](docs/correlations/tube_banks.rst).

---

## Development Setup

```bash
git clone <your-repo-url>
cd htcie
uv sync
uv run pytest
uv run htcie --help
```

---

## Running Tests

```bash
uv run pytest tests/ -v
```

---

## Building Docs

```bash
uv run python docs/build_docs.py
# or
uv run sphinx-build docs/ docs/build/html
```

---

## Roadmap

The open core covers single-phase forced convection (internal tubes, external cylinders and plates, tube banks). Planned work includes:

- **Domain expansion** — boiling, condensation, and two-phase convection are the primary domain targets beyond the current single-phase forced convection scope.

- **Confidence improvements** — the current confidence class is based on inter-method spread. Planned improvements include benchmark-calibrated uncertainty bounds (replacing the textbook-consensus estimates currently flagged `UNCERTAIN` in the catalog), richer literature error metadata, and finer-grained extrapolation penalties tied to distance from validated Re/Pr ranges.

- **Fluid property library** — users currently supply all fluid properties (density, viscosity, conductivity, heat capacity) explicitly. A built-in fluid library would resolve common fluids (water, air, common refrigerants, thermal oils) at a given temperature, reducing the input burden and eliminating a common source of user error.

- **Pro tier** — beyond the hosted API already available, a Pro tier would add: batch evaluation (submit multiple operating states in a single request), extended correlation coverage (additional geometries and fluids beyond the 13 MVP correlations), custom scoring weight profiles (adjust the ranking criteria to reflect your organisation's validation standards), and richer export formats (PDF reports with charts, Excel summaries).

Commercial licensing is available for organizations that cannot use the AGPL v3 terms (see License section).

---

## License

GNU Affero General Public License v3.0. See `LICENSE`.

For embedded or closed-source use where AGPL v3 is not compatible with your licensing requirements, contact the project maintainers.

