Scoring
=======

Scoring v1
----------

htcie uses a versioned scoring model to rank applicable correlations. The
current model is **Scoring v1**, which evaluates eight factors and combines
them into a total score via explicit weights.

Factors
^^^^^^^

1. **Validity fit** (weight 0.30) — How well the operating point sits within
   the centre of the correlation's stated :math:`Re` range. Score is 1.0 at
   the midpoint of :math:`[Re_{min}, Re_{max}]` and falls linearly to 0 at
   the edges.

2. **Geometry match** (weight 0.20) — 1.0 if the correlation's required
   ``geometry_type`` matches the state; 0.0 otherwise.

3. **Regime match** (weight 0.15) — 1.0 if the correlation's declared flow
   regime (laminar / turbulent / transitional_turbulent / all) matches the
   regime inferred from :math:`Re`; 0.2 partial credit otherwise.

4. **Boundary-condition match** (weight 0.10) — 1.0 if the specified boundary
   condition (UWT or UHF) is in the correlation's ``boundary_conditions``
   list; 0.5 if the correlation has no stated preference.

5. **Correction completeness** (weight 0.10) — Base score 0.5; +0.25 if the
   correlation supports a viscosity-ratio correction and ``wall_viscosity`` is
   provided; +0.25 if it handles entry-length effects and ``developing_length``
   is provided.

6. **Pedigree** (weight 0.10) — Source quality proxy based on publication year:
   0.9 for year ≥ 1970, 0.7 for year ≥ 1950, 0.5 otherwise. A +0.1 bonus
   (capped at 1.0) is applied to ``internal.gnielinski`` and
   ``internal.petukhov`` in recognition of their broad validation base and
   lowest stated uncertainty.

7. **Uncertainty score** (weight 0.05) — 1.0 if ``literature_uncertainty_pct``
   ≤ 10 %; 0.7 if ≤ 20 %; 0.4 if > 20 %; 0.5 if not reported.

8. **Extrapolation penalty** (weight −0.30, subtracted) — Grows with the
   fractional distance outside the valid :math:`Re` range. Penalty is
   :math:`\min(0.5,\, (Re - Re_{max}) / Re_{max})` above the upper bound, and
   analogously below the lower bound. Maximum combined penalty is 1.0.

Score formula
^^^^^^^^^^^^^

.. math::

   \text{score} = 0.30 \cdot f_\text{validity}
                + 0.20 \cdot f_\text{geometry}
                + 0.15 \cdot f_\text{regime}
                + 0.10 \cdot f_\text{boundary}
                + 0.10 \cdot f_\text{corrections}
                + 0.10 \cdot f_\text{pedigree}
                + 0.05 \cdot f_\text{uncertainty}
                - 0.30 \cdot p_\text{extrapolation}

The seven positive-factor weights sum to 1.0. The extrapolation penalty is
an independent subtraction and can drive the score below zero.

Versioning
^^^^^^^^^^

Scoring weights are stored in ``ScoringWeightsV1`` in
``htcie/core/ranking.py``. Each ``HtcieReport`` records the
``scoring_weights_version`` field so that any stored report can be
re-interpreted alongside the weights that produced it. Changing the weights
requires bumping the version string and updating both this document and the
associated tests.

Previous version
^^^^^^^^^^^^^^^^

Scoring v0 used three factors (validity fit, pedigree placeholder, geometry
match) and is documented in ``docs/scoring/v0.md``.
