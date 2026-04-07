# htcie — Notebooks

Three self-contained JupyterLab notebooks. Each runs independently against the installed `htcie` package and loads correlations via `build_registry()` from the installed `htcie` package.

## Launch

```bash
uv run jupyter lab
```

## Notebooks

| File | Purpose | Audience |
|------|---------|---------|
| [benchmark.ipynb](benchmark.ipynb) | Verify all 13 correlations against Incropera textbook reference values (14/14 cases pass) | Technical validation |
| [examples.ipynb](examples.ipynb) | Step-by-step usage guide: state construction, pipeline stages, applicability, evaluations, ranking, explanation, velocity sweep | New htcie users |
| [gtm_demo.ipynb](gtm_demo.ipynb) | Narrative demo: from manual Dittus-Boelter to full correlation intelligence — all 4 differentiators | Engineers, stakeholders |

## Sample input

`sample_internal_convection_input.json` — water in a 10 mm circular tube at 2 m/s (Re ≈ 22 400, Pr ≈ 6.2). Used by `examples.ipynb`.
