Quickstart
==========

Pipeline (recommended)
-----------------------

The simplest way to run a full evaluation is via ``run_evaluation``, which
chains all seven pipeline layers and returns a serialisable ``HtcieReport``:

.. code-block:: python

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
       print(report.explanation.to_text())   # human-readable recommendation
       print(report.to_dict())               # full JSON-serialisable audit trail

Python API (step-by-step)
-------------------------

For finer control, call each engine directly:

.. code-block:: python

   from htcie.core.applicability import ApplicabilityEngine
   from htcie.core.evaluator import EvaluationEngine
   from htcie.core.ranking import RankingEngine

   applicable = ApplicabilityEngine().evaluate(state, registry.all())
   evaluations = [EvaluationEngine().evaluate(state, m) for m in applicable.applicable]
   ranked = RankingEngine().rank(state, applicable.applicable)

   print(f"Best method: {ranked[0].key} (score: {ranked[0].score:.3f})")
   for key, reason in [(m.key, r) for m, r in applicable.excluded]:
       print(f"  Excluded {key}: {reason}")

CLI
---

.. code-block:: bash

   # Run evaluation from a JSON file, print JSON result
   htcie evaluate state.json

   # Save as Markdown report
   htcie evaluate state.json --output report.md --markdown

   # Browse available correlations
   htcie methods list
   htcie methods list --family convection_internal
   htcie methods show internal.gnielinski

REST API
--------

Start the server:

.. code-block:: bash

   uvicorn htcie.api.main:app --reload

   # Or with a custom data directory:
   HTCIE_DATA_DIR=/path/to/data uvicorn htcie.api.main:app

Available endpoints:

.. code-block:: bash

   # Run evaluation
   POST /evaluate       body: {"state": {...}}

   # Browse correlations
   GET  /methods
   GET  /methods?family=convection_internal
   GET  /methods/families
   GET  /methods/internal.gnielinski

   # Health check
   GET  /health

Web GUI
-------

.. code-block:: bash

   htcie gui

Opens the NiceGUI interface at ``http://localhost:8080``. Requires the
``nicegui`` extra (``uv add nicegui``).

Report output
-------------

``HtcieReport.to_dict()`` returns a JSON-serialisable dict containing:

- ``applicable`` — list of correlation keys that passed applicability checks
- ``excluded`` — list of ``{key, reason}`` dicts for filtered-out correlations
- ``evaluations`` — list of ``{key, value, metadata}`` Nusselt-number results
- ``ranking`` — list of ``{key, score, breakdown}`` with per-factor scores
- ``spread`` — inter-method spread statistics (mean, stdev, relative_spread)
- ``confidence`` — ``"high"``, ``"medium"``, or ``"low"``
- ``explanation`` — structured recommendation with text rendering

``evaluations`` entries also include ``h``, ``h_low``, ``h_high``,
``uncertainty_pct``, and ``uncertainty_note`` from the uncertainty engine.

Save as JSON, Markdown, or self-contained HTML:

.. code-block:: python

   from htcie.reports.serializers import (
       dump_json_report,
       dump_markdown_report,
       dump_html_report,
   )

   dump_json_report(report, "result.json")
   dump_markdown_report(report, "result.md")
   dump_html_report(report, "result.html")  # self-contained, no external deps
