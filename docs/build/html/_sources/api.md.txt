# htcie API Reference

This guide is written for engineers who want to use htcie programmatically.
You do not need to be a software developer — every step is explained in plain language,
with complete examples you can copy and run immediately.

---

## What the API does

You describe a heat-transfer problem (fluid properties, geometry, flow conditions),
and the API returns:

- every correlation that applies to your conditions
- which ones were filtered out and **why**
- the Nusselt number computed by each applicable correlation
- a ranked recommendation (best match first) with a score breakdown
- an overall confidence rating based on how much the methods agree
- a plain-language explanation of the ranking decision

---

## Base URL

All requests go to:

```
https://htcie-api.onrender.com
```

### First-time note on the free tier

If the service has been idle, the first request may take **20–30 seconds** to
respond while the server wakes up. This is normal. Subsequent requests are fast.

---

## Authentication

**None required.** All current correlations are publicly accessible with no
API key or login.

---

## Interactive explorer

FastAPI automatically generates an interactive documentation page at:

```
https://htcie-api.onrender.com/docs
```

Open this URL in any browser. You will see a list of every endpoint. Click on
one, fill in the fields, and click **Execute** to run a live request — no
`curl` or Python required. This is the easiest way to explore the API for the
first time.

---

## Endpoints

### 1. Check the server is running — `GET /health`

Use this to confirm the API is up before sending calculations.

**Request:** no input needed.

```bash
curl https://htcie-api.onrender.com/health
```

**Response:**

```json
{"status": "ok", "project": "htcie", "version": "0.1.0"}
```

If you get this response, the API is running correctly.

---

### 2. List available correlations — `GET /methods`

Use this to see which heat-transfer correlations are available.

```bash
curl https://htcie-api.onrender.com/methods
```

**Response:** a list of all correlation entries. Each entry shows the correlation
name, its source reference, and the validity range (Re, Pr bounds).

---

### 3. Run an evaluation — `POST /evaluate`

This is the main endpoint. You describe the engineering problem and htcie
returns a complete analysis.

#### How to structure your request

The request body is a JSON object with a single key `"state"`, which contains
four sections: `fluid`, `geometry`, `boundary`, and `flow`.

#### Field reference

**`state.fluid` — thermophysical properties of the working fluid**

| Field | Required | Unit | Description |
|---|---|---|---|
| `density` | yes | kg/m³ | Fluid density at bulk temperature |
| `viscosity` | yes | Pa·s | Dynamic viscosity at bulk temperature |
| `thermal_conductivity` | yes | W/m·K | Thermal conductivity at bulk temperature |
| `heat_capacity` | yes | J/kg·K | Specific heat capacity at constant pressure |
| `wall_viscosity` | no | Pa·s | Dynamic viscosity at wall temperature — only needed for Sieder-Tate correction |

**`state.geometry` — description of the heat-transfer surface**

| Field | Required | Unit | Description |
|---|---|---|---|
| `geometry_type` | yes | — | One of the four values in the table below |
| `characteristic_length` | yes | m | Tube inner diameter, cylinder diameter, or plate length |
| `hydraulic_diameter` | no | m | For circular tubes: same as `characteristic_length`; omit for other geometries |
| `roughness` | no | m | Surface roughness; defaults to 0 (smooth) |
| `pitch_transverse` | no* | m | For tube banks: centre-to-centre distance perpendicular to flow |
| `pitch_longitudinal` | no* | m | For tube banks: centre-to-centre distance parallel to flow |
| `arrangement` | no* | — | For tube banks: `"inline"` or `"staggered"` |

*Required when `geometry_type` is `"tube_bank"`.

**Valid `geometry_type` values:**

| Value | Use for |
|---|---|
| `"circular_tube"` | Flow inside a round tube or pipe |
| `"cylinder_crossflow"` | Flow over the outside of a single cylinder |
| `"flat_plate"` | Flow over a flat plate |
| `"tube_bank"` | Flow across an array of tubes |

**`state.boundary` — thermal boundary condition at the surface**

| Field | Required | Description |
|---|---|---|
| `boundary_type` | yes | `"constant_heat_flux"` (uniform heating rate) or `"constant_wall_temperature"` (isothermal surface) |
| `wall_temperature` | no | Wall temperature in K — used with `constant_wall_temperature` |
| `bulk_temperature` | no | Fluid bulk temperature in K — used for automatic heating/cooling detection |

**`state.flow` — flow conditions**

| Field | Required | Unit | Description |
|---|---|---|---|
| `velocity` | yes | m/s | Mean flow velocity (bulk average) |
| `mass_flow_rate` | no | kg/s | Alternative to velocity for some configurations |
| `developing_length` | no | m | Axial position from the inlet — enables entry-length corrections |

---

#### Worked example: air flowing inside a tube

**Conditions:**
- Air at 60 °C (bulk temperature)
- Tube inner diameter: 25 mm
- Tube length: 2 m
- Mean velocity: 5 m/s
- Uniform heat flux boundary

**`curl` command:**

```bash
curl -X POST https://htcie-api.onrender.com/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "state": {
      "fluid": {
        "density": 1.060,
        "viscosity": 1.96e-5,
        "thermal_conductivity": 0.030,
        "heat_capacity": 1007.0
      },
      "geometry": {
        "geometry_type": "circular_tube",
        "characteristic_length": 0.025,
        "hydraulic_diameter": 0.025
      },
      "boundary": {
        "boundary_type": "constant_heat_flux"
      },
      "flow": {
        "velocity": 5.0
      }
    }
  }'
```

**Response structure (key fields):**

```json
{
  "engine_version": "0.1.0",
  "timestamp": "2024-01-15, 14:32:01",
  "input_state": { "fluid": {}, "geometry": {}, "boundary": {}, "flow": {} },
  "derived": {
    "reynolds": 8027.6,
    "prandtl": 0.714,
    "graetz": null,
    "entry_length_ratio": null,
    "pitch_ratio_transverse": null,
    "pitch_ratio_longitudinal": null
  },
  "applicable": ["gnielinski", "dittus_boelter"],
  "excluded": [
    { "key": "shah_laminar", "reason": "Re = 8027.6 outside validity range [0, 2300]" }
  ],
  "evaluations": [
    {
      "key": "gnielinski",
      "value": 42.3,
      "uncertainty_pct": 10.0,
      "h": 50840.0,
      "h_low": 45756.0,
      "h_high": 55924.0,
      "uncertainty_note": "±10% per Gnielinski (1976)",
      "metadata": {}
    }
  ],
  "ranking": [
    { "key": "gnielinski", "score": 0.91, "breakdown": { "validity_fit": 0.95, "...": "..." } },
    { "key": "dittus_boelter", "score": 0.74, "breakdown": { "...": "..." } }
  ],
  "spread": { "count": 2, "mean": 41.2, "stdev": 1.1, "relative_spread": 0.027 },
  "confidence": "high",
  "explanation": {
    "best_method": "gnielinski",
    "best_score": 0.91,
    "score_breakdown": { "validity_fit": 0.95, "...": "..." },
    "why_applicable": ["gnielinski is applicable for the given Re, Pr, and geometry."],
    "why_others_excluded": [{ "key": "shah_laminar", "reason": "..." }],
    "key_assumptions": ["Fully developed turbulent flow", "Smooth tube wall"],
    "confidence_class": "high",
    "extrapolation_warnings": [],
    "recommendation_note": "Use gnielinski — highest score (0.910) for the given operating conditions.",
    "text": "Recommended method: gnielinski\nScore: 0.910\n..."
  },
  "scoring_weights_version": "v1"
}
```

**Reading the response:**

- `ranking[0]` is the **best correlation for your conditions**. Look up its `key` in `evaluations` to get the Nusselt number (`value`), heat transfer coefficient (`h`), and uncertainty band (`h_low` / `h_high`).
- `confidence` is a plain string: `"high"` (< 10% spread), `"medium"` (10–25%), or `"low"` (> 25%). Low confidence means the methods disagree significantly — double-check your inputs or consult a reference.
- `excluded` explains which correlations were filtered out and why — useful for understanding the limits of your operating conditions.
- `explanation.text` is a pre-rendered, human-readable summary. `explanation.recommendation_note` is a single-sentence version.

---

#### Worked example: air flow over a cylinder

**Conditions:**
- Air at 25 °C
- Cylinder diameter: 50 mm
- Free-stream velocity: 8 m/s
- Isothermal surface

```bash
curl -X POST https://htcie-api.onrender.com/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "state": {
      "fluid": {
        "density": 1.184,
        "viscosity": 1.849e-5,
        "thermal_conductivity": 0.0262,
        "heat_capacity": 1007.0
      },
      "geometry": {
        "geometry_type": "cylinder_crossflow",
        "characteristic_length": 0.050
      },
      "boundary": {
        "boundary_type": "constant_wall_temperature"
      },
      "flow": {
        "velocity": 8.0
      }
    }
  }'
```

---

#### Common errors

| HTTP status | Meaning | What to check |
|---|---|---|
| `200 OK` | Success | Read the response body |
| `422 Unprocessable Entity` | Invalid input | Check required fields and value ranges; the response body explains which field failed |
| `500 Internal Server Error` | Server fault | Check that `density`, `viscosity`, etc. are positive finite numbers |

---

## Calling the API from Python

Install the `httpx` library if you don't have it:

```bash
pip install httpx
```

```python
import httpx

payload = {
    "state": {
        "fluid": {
            "density": 1.060,
            "viscosity": 1.96e-5,
            "thermal_conductivity": 0.030,
            "heat_capacity": 1007.0,
        },
        "geometry": {
            "geometry_type": "circular_tube",
            "characteristic_length": 0.025,
            "hydraulic_diameter": 0.025,
        },
        "boundary": {
            "boundary_type": "constant_heat_flux",
        },
        "flow": {
            "velocity": 5.0,
        },
    }
}

response = httpx.post(
    "https://htcie-api.onrender.com/evaluate",
    json=payload,
    timeout=60,  # allow time for cold start on free tier
)
response.raise_for_status()
report = response.json()

# Best correlation result
best_key = report["ranking"][0]["key"]
best_eval = next(e for e in report["evaluations"] if e["key"] == best_key)
print(f"Recommended correlation : {best_key}")
print(f"Nusselt number          : {best_eval['value']:.2f}")
print(f"Confidence              : {report['confidence']}")
print(f"Summary                 : {report['explanation']['recommendation_note']}")
```

---

## Units summary

All inputs and outputs use SI units throughout.

| Quantity | Unit |
|---|---|
| Length, diameter | m |
| Velocity | m/s |
| Density | kg/m³ |
| Dynamic viscosity | Pa·s |
| Thermal conductivity | W/m·K |
| Specific heat | J/kg·K |
| Temperature | K |
| Mass flow rate | kg/s |
| Nusselt number | dimensionless |
