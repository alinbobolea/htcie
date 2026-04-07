# Correlation Metadata Schema

Each correlation is defined in a YAML file under `data/correlations/` and
validated against the `CorrelationMetadata` Pydantic model on registry load.

## Required fields

| Field | Type | Description |
|---|---|---|
| `key` | `str` | Dot-namespaced identifier, e.g. `internal.gnielinski`. Must be unique across all files. |
| `family` | `str` | Domain family: `convection_internal`, `convection_external`, or `tube_banks`. |
| `title` | `str` | Human-readable name including author and year, e.g. `"Gnielinski (1976)"`. |
| `output` | `str` | Physical quantity produced, typically `"Nu"`. |
| `source` | `dict` | Bibliographic reference with keys `authors` (list), `year` (int), `title`, `journal`, `doi`. |
| `assumptions` | `list[str]` | Stated assumptions (smooth tube, uniform properties, fully developed flow, etc.). |
| `validity` | `dict` | Bounds used for applicability filtering (see below). |

## Optional fields

| Field | Type | Default | Description |
|---|---|---|---|
| `formula_latex` | `str` | `""` | LaTeX string of the primary correlation formula. Used by the GUI and docs. |
| `flow_regime` | `str` | `"all"` | Applicable regime: `"laminar"`, `"turbulent"`, `"transitional_turbulent"`, or `"all"`. |
| `boundary_conditions` | `list[str]` | `[]` | Applicable boundary types: `"constant_wall_temperature"`, `"constant_heat_flux"`, or both. Empty list means no preference. |
| `required_inputs` | `list[str]` | `[]` | Dimensionless groups or inputs required, e.g. `["Reynolds", "Prandtl"]`. |
| `literature_uncertainty_pct` | `float \| null` | `null` | Stated accuracy from the source, in percent. Feeds the uncertainty score in ranking. |
| `notes` | `list[str]` | `[]` | Implementation notes, known limitations, or guidance on when to prefer this correlation. |

## Validity dict keys

The `validity` dict is checked by `ApplicabilityEngine`. All keys are optional.

| Key | Type | Description |
|---|---|---|
| `geometry_type` | `str` | Required geometry: `circular_tube`, `cylinder_crossflow`, `flat_plate`, or `tube_bank`. |
| `re_min` | `float` | Minimum Reynolds number (exclusive). |
| `re_max` | `float` | Maximum Reynolds number (exclusive). |
| `pr_min` | `float` | Minimum Prandtl number. |
| `pr_max` | `float` | Maximum Prandtl number. |
| `ld_min` | `float` | Minimum $L/D$ (entry length ratio), informational only — not enforced by the engine. |

## Example

```yaml
key: internal.gnielinski
family: convection_internal
title: "Gnielinski (1976)"
output: Nu
formula_latex: >
  Nu = \frac{(f/8)(Re - 1000)\,Pr}{1 + 12.7\sqrt{f/8}(Pr^{2/3} - 1)}
flow_regime: transitional_turbulent
boundary_conditions:
  - constant_wall_temperature
  - constant_heat_flux
required_inputs:
  - Reynolds
  - Prandtl
validity:
  geometry_type: circular_tube
  re_min: 3000
  re_max: 5000000
  pr_min: 0.5
  pr_max: 2000
  ld_min: 10
literature_uncertainty_pct: 10
assumptions:
  - Smooth circular tube
  - Fully turbulent or transitional flow (Re > 3000)
  - Constant fluid properties evaluated at bulk temperature
source:
  authors:
    - "Gnielinski, V."
  year: 1976
  title: "New equations for heat and mass transfer in turbulent pipe and channel flow"
  journal: "International Chemical Engineering"
  doi: ""
notes:
  - Preferred over Dittus-Boelter for Re 3000–5e6 due to lower stated uncertainty (~10 %)
  - Uses Petukhov (1970) friction factor f = (0.790 ln Re - 1.64)^{-2}
```

## Engineering trust rules

Every entry must include `source`, `assumptions`, `validity`, and `notes`.
If a ranking or confidence behaviour changes, update both the YAML and any
affected tests. Never invent a validity range or uncertainty figure without a
literature citation.
