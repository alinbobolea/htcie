Architecture Overview
=====================

htcie is implemented as a layered deterministic system. Each layer has a
single responsibility and produces a serializable output that can be audited
independently.

The seven layers are:

1. **State** — The canonical ``EngineeringState`` object captures fluid
   properties, geometry, boundary conditions, and flow state. It is the
   single source of truth passed through all layers.

2. **Registry** — The ``CorrelationRegistry`` loads correlation metadata from
   ``data/correlations/*.yaml`` at startup. Each entry describes the
   correlation's formula, validity rules, required inputs, assumptions, and
   source.

3. **Applicability** — The ``ApplicabilityEngine`` filters the registry to
   correlations whose validity ranges and geometry requirements match the
   current state. Excluded correlations are returned with explicit reasons.

4. **Evaluation** — The ``EvaluationEngine`` computes the Nusselt number (and
   derived quantities) for each applicable correlation, given the state.

5. **Ranking** — The ``RankingEngine`` scores applicable correlations using
   the versioned scoring model (see :doc:`scoring`) and returns an ordered
   list with scores.

6. **Confidence / Uncertainty** — The uncertainty layer combines
   literature-reported accuracy, extrapolation distance, and regime fidelity
   into a confidence interval for each result.

7. **Explanation and Reporting** — The explanation layer produces a
   human-readable audit trail: which correlations were considered, why others
   were excluded, what score each received, and the resulting recommendation.

See also the source file ``docs/architecture/overview.md`` for the original
design notes.
