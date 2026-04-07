Tube Banks
==========

Two correlations for crossflow over tube banks (bundles). Both require the
transverse pitch :math:`S_T`, longitudinal pitch :math:`S_L`, and an explicit
``arrangement`` field (``"inline"`` or ``"staggered"``). The ``arrangement``
field is required on the ``Geometry`` object when ``geometry_type = "tube_bank"``.

All correlations output the Nusselt number :math:`Nu = h D / k`, where
:math:`D` is the tube outer diameter.

.. list-table::
   :header-rows: 1
   :widths: 30 35 20 10 5

   * - Key
     - Title
     - Re Range
     - Pr Range
     - Year
   * - ``tube_banks.zukauskas``
     - Žukauskas Bank
     - 20 – 2,000,000
     - 0.7 – 500
     - 1972
   * - ``tube_banks.grimison``
     - Grimison
     - 2,000 – 40,000
     - Pr ≈ 0.7
     - 1937

Correlation formulas
--------------------

**Žukauskas (1972)** — ``tube_banks.zukauskas``

.. math::

   Nu = C\,Re_D^m\,Pr^{0.36}\,\left(\frac{Pr}{Pr_w}\right)^{0.25}\,F

Tabular coefficients :math:`C` and :math:`m` depend on arrangement (inline
or staggered) and Re band. For staggered arrangements at :math:`Re \geq 1000`,
:math:`C` includes a pitch-ratio factor :math:`(S_T/S_L)^{0.2}`.

The wall-Prandtl correction :math:`(Pr/Pr_w)^{0.25}` is omitted (set to 1)
when ``fluid.wall_viscosity`` is not provided. The row correction factor
:math:`F = 1.0` (full correction tables require a number-of-rows input not
present in the current state model).

**Grimison (1937)** — ``tube_banks.grimison``

.. math::

   Nu = C_1\,Re_D^{m_1}\,Pr^{0.36}

Uses simplified constants from Incropera/DeWitt Table 7.4 (historical).
Valid for :math:`2000 \leq Re \leq 40{,}000`; developed from gas data
(Pr ≈ 0.7 only). No wall-temperature correction is applied.

Notes
-----

- Both correlations require ``geometry.pitch_transverse`` and
  ``geometry.pitch_longitudinal`` to be set; the state validator enforces this
  for ``geometry_type = "tube_bank"``.
- ``tube_banks.zukauskas`` is preferred over Grimison for its wider Re range,
  wall-Prandtl correction, and broader validation base.
- ``tube_banks.grimison`` is retained for legacy comparison and for Re bands
  not covered by other tube-bank correlations.
- The row correction factor :math:`F` (which reduces :math:`Nu` for banks with
  fewer than ~10 rows) is not currently applied. Results represent the
  fully-developed average over a deep bank.

References
----------

Formulation (equations)
~~~~~~~~~~~~~~~~~~~~~~~

**Žukauskas (1972)**: Žukauskas, A., "Heat Transfer from Tubes in Crossflow," in *Advances in
Heat Transfer*, vol. 8, eds. Hartnett, J.P. and Irvine, T.F., Academic Press, New York,
pp. 93–160, 1972, DOI: 10.1016/S0065-2717(08)70038-8. Full volume PDF available (Internet
Archive, identifier AdvancesInHeatTransfer). Updated revision: Žukauskas, A., *Advances in
Heat Transfer*, vol. 18, pp. 87–159, 1987, DOI: 10.1016/S0065-2717(08)70166-7 (paywalled).
Textbook: Incropera, F.P., DeWitt, D.P., Bergman, T.L., and Lavine, A.S., *Fundamentals of
Heat and Mass Transfer*, 7th ed., Wiley, 2011, Sec. 7.6, Tables 7.5–7.7, p. 446.

**Grimison (1937)**: Grimison, E.D., "Correlation and utilization of new data on flow resistance
and heat transfer for cross flow of gases over tube banks," *Transactions of the ASME*, vol. 59,
no. 7, pp. 583–594, Oct. 1937, DOI: 10.1115/1.4020557. (ASME Digital Collection paywall.)
Experimental data from: Pierson, O.L., "Experimental investigation of the influence of tube
arrangement on convection heat transfer and flow resistance in cross flow of gases over tube
banks," *Transactions of the ASME*, vol. 59, no. 7, pp. 563–572, 1937,
DOI: 10.1115/1.4020549. Textbook: Incropera et al., 7th ed., Sec. 7.6, Table 7.4 (historical);
Cengel, Y.A. and Ghajar, A.J., *Heat and Mass Transfer*, 5th ed., McGraw-Hill, 2015, Sec. 7-4.

Variable definitions
~~~~~~~~~~~~~~~~~~~~

- :math:`Nu = h D / k` (Nusselt number, tube outer diameter :math:`D`):
  Incropera et al., 7th ed., Sec. 7.6.
- :math:`Re_D` based on maximum free-stream velocity :math:`V_{max}` in the minimum
  free-flow area between tubes: Žukauskas (1972), p. 93; Incropera et al., 7th ed.,
  Sec. 7.6.
- :math:`Pr` evaluated at fluid inlet/outlet arithmetic mean temperature (Žukauskas bank):
  Incropera et al., 7th ed., Sec. 7.6, p. 446.
- :math:`Pr_w` evaluated at tube wall surface temperature :math:`T_s` (Žukauskas bank):
  Žukauskas (1972); Incropera et al., 7th ed., Table 7.5, p. 446.
- :math:`C`, :math:`m` (tabular coefficients, both correlations): Incropera et al., 7th ed.,
  Tables 7.5–7.6 (Žukauskas bank) and Table 7.4 historical (Grimison); Žukauskas (1972).
- :math:`F` (row correction factor for :math:`N_L < 20`): Žukauskas (1972);
  Incropera et al., 7th ed., Table 7.7, p. 446. Set to 1.0 in this implementation (see Notes).
- :math:`S_T`, :math:`S_L` (transverse and longitudinal pitch): Incropera et al., 7th ed.,
  Sec. 7.6.

Range of applicability
~~~~~~~~~~~~~~~~~~~~~~

- **Žukauskas bank** Re 20–2,000,000; Pr 0.7–500; :math:`N_L \geq 20` for :math:`F = 1`.
  The lower bound Re = 20 is confirmed directly from the primary source: Žukauskas (1972),
  p. 147 explicitly states Eqs. (38)–(44) describe "49 banks…at Re from 20 to 2×10\ :sup:`6`
  and Pr from 0.7 to 500." Three-source discrepancy: the correlation YAML previously recorded
  :math:`Re_{min} = 10`; the Incropera text records :math:`Re_D = 16`; the primary source
  p. 147 states Re = 20. The primary source is taken as authoritative and the YAML has been
  corrected accordingly.
- **Grimison** Re 2,000–40,000; Pr ≈ 0.7 (gases only). The valid range is sourced from
  Incropera et al., 7th ed., Sec. 7.6, Table 7.4 and Cengel & Ghajar, 5th ed., Sec. 7-4.
  The primary source (Grimison 1937, Trans. ASME 59:583–594, DOI: 10.1115/1.4020557) is
  paywalled and unverifiable; the range Re 2,000–40,000 is a textbook-attributed bound.
  **UNCERTAIN** — primary source not accessible.

Assumptions
~~~~~~~~~~~

- :math:`Re_D` based on maximum velocity :math:`V_{max}` between tubes (Žukauskas bank):
  Žukauskas (1972), p. 93; Incropera et al., 7th ed., Sec. 7.6.
- Fluid properties at arithmetic mean of inlet and outlet temperatures; :math:`Pr_w` at
  wall temperature (Žukauskas bank): Incropera et al., 7th ed., Sec. 7.6, p. 446.
- :math:`N_L \geq 20` rows for full validity (:math:`F = 1.0`); row correction factor from
  Table 7.7 required for shallower banks: Žukauskas (1972); Incropera et al., 7th ed.,
  Table 7.7.
- For Re 100–1,000 (Žukauskas bank) treat as single isolated cylinder (no bank
  coefficients tabulated): Incropera et al., 7th ed., Table 7.5.
- :math:`S_T / S_L \geq 0.7` required for aligned (in-line) arrangement:
  Incropera et al., 7th ed., Table 7.5, note.
- No wall Prandtl correction applied (Grimison): Grimison (1937) original data was for
  gases with Pr ≈ 0.7 only; the :math:`Pr^{0.36}` factor in the textbook form is a
  later generalization — see Flag below.
- Inline vs. staggered arrangement supplied explicitly via the ``arrangement`` field on
  ``Geometry``; this is a required input for ``geometry_type = "tube_bank"`` (state
  validator enforces it). Not inferred from pitch ratios.

Uncertainty / error bounds
~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Žukauskas bank ±25%**: textbook-attributed figure (Incropera 7th ed., Sec. 7.6;
  Cengel & Ghajar, 5th ed., Sec. 7-4). The primary source
  (Žukauskas 1972, "Heat Transfer from Tubes in Crossflow," *Advances in Heat Transfer*, Vol. 8, pp. 93–160) was reviewed in full during the
  2026-03-28 traceability audit. No explicit ±% uncertainty statement was found for the
  tube-bank correlation in that chapter. **UNCERTAIN** — primary source reviewed; no
  explicit bound found.
- **Grimison ±25%**: textbook-attributed. Primary source (Grimison 1937) is paywalled
  (ASME Digital Collection, DOI: 10.1115/1.4020557) and unverifiable.
  **UNCERTAIN** — primary source not accessible.

Missing references
~~~~~~~~~~~~~~~~~~

None identified beyond those flagged under individual entries below.

Traceability mapping
~~~~~~~~~~~~~~~~~~~~

- **Žukauskas bank equation form** :math:`C\,Re_D^m\,Pr^{0.36}\,(Pr/Pr_w)^{0.25}\,F` →
  Žukauskas (1972), Adv. Heat Transfer 8:93–160; Incropera et al., 7th ed., Sec. 7.6,
  Tables 7.5–7.7, p. 446.
- **Žukauskas bank C, m tabular coefficients (inline and staggered, Re bands)** →
  Incropera et al., 7th ed., Tables 7.5–7.6, p. 446, sourced from Žukauskas (1972).
  Primary source Eqs. (38)–(44) verified against Žukauskas (1972), "Heat Transfer from Tubes
  in Crossflow," *Advances in Heat Transfer*, Vol. 8 (pp. 142–147). Verified coefficients: Aligned Re 20–100: C=0.80, m=0.40; Staggered
  Re 20–100: C=0.90, m=0.40; Aligned Re 1,000–200,000: C=0.27, m=0.63; Staggered
  Re 1,000–200,000:
  C=0.35×(:math:`S_T/S_L`)\ :sup:`0.2`, m=0.60 (:math:`S_T/S_L < 2`); C=0.40, m=0.60
  (:math:`S_T/S_L \geq 2`); Aligned Re 200,000–2,000,000: C=0.021, m=0.84; Staggered
  Re 200,000–2,000,000: C=0.022, m=0.84.
- **Žukauskas bank Pr exponent 0.36** → Žukauskas (1972); Incropera et al., 7th ed.,
  Tables 7.5–7.6.
- **Žukauskas bank** :math:`(Pr/Pr_w)^{0.25}` **correction** → Žukauskas (1972);
  Incropera et al., 7th ed., Sec. 7.6.
- **Žukauskas bank staggered pitch factor** :math:`(S_T/S_L)^{0.2}` **for Re ≥ 1,000** →
  Incropera et al., 7th ed., Table 7.6; Žukauskas (1972).
- **Row correction factor** :math:`F = 1.0` **(for** :math:`N_L \geq 20` **)** →
  Žukauskas (1972); Incropera et al., 7th ed., Table 7.7, p. 446.
- **Žukauskas bank Re 20–2,000,000; Pr 0.7–500** → Žukauskas (1972), p. 147 (primary
  source, confirmed); Incropera et al., 7th ed., Sec. 7.6, p. 446 (documents Re ≥ 16 —
  slightly inconsistent with primary source).
- **Žukauskas bank** :math:`N_L \geq 20` **for full validity** → Žukauskas (1972);
  Incropera et al., 7th ed., Sec. 7.6, Table 7.7.
- **Grimison equation form** :math:`C_1\,Re_D^{m_1}\,Pr^{0.36}` → Incropera et al.,
  7th ed., Sec. 7.6 (historical table). **Flag: the Pr\ :sup:`0.36` factor is not present
  in the original Grimison (1937) paper, which was developed for gases (Pr ≈ 0.7) only.
  This generalization to other fluids via Pr\ :sup:`0.36` originates in the textbook form
  (Incropera et al.) and is not traceable to Grimison (1937) directly.**
- **Grimison C1, m1 constants** → Incropera et al., 7th ed., Sec. 7.6, Table 7.4
  (historical); Cengel & Ghajar, 5th ed., Sec. 7-4; ultimately Grimison (1937), Trans.
  ASME 59:583–594, DOI: 10.1115/1.4020557.
- **Grimison Re 2,000–40,000** → Incropera et al., 7th ed., Sec. 7.6, Table 7.4;
  Cengel & Ghajar, 5th ed., Sec. 7-4. Primary source (Grimison 1937, Trans. ASME
  59:583–594) is paywalled; range is textbook-attributed only. **UNCERTAIN.**
- **Grimison — no wall Prandtl correction** → Grimison (1937) original data for gases;
  Incropera et al., 7th ed., Sec. 7.6.
- **Arrangement (inline / staggered) as explicit required input** → project implementation
  decision (see dev-log 2026-03-27). The ``arrangement`` field on ``Geometry`` is
  required when ``geometry_type = "tube_bank"``; it is not inferred from pitch ratios.
  Inline/staggered terminology follows Incropera et al., 7th ed., Sec. 7.6.
- **Žukauskas bank uncertainty ±25%** → **UNCERTAIN** (specific primary-source page not
  identified).
- **Grimison uncertainty ±25%** → **UNCERTAIN** (specific primary-source page not
  identified).
