External Forced Convection
==========================

Five correlations for external forced convection over cylinders and flat plates.
All correlations output the Nusselt number :math:`Nu = h L / k`, where :math:`L`
is the characteristic length (outer diameter :math:`D` for cylinders, plate
length :math:`L` for plates).

.. list-table::
   :header-rows: 1
   :widths: 32 30 22 8 8

   * - Key
     - Title
     - Re Range
     - Pr Range
     - Year
   * - ``external.churchill_bernstein``
     - Churchill-Bernstein (cylinder)
     - All Re (composite)
     - ≥ 0.2
     - 1977
   * - ``external.zukauskas_cylinder``
     - Žukauskas (cylinder)
     - 1 – 1,000,000
     - 0.7 – 500
     - 1972
   * - ``external.hilpert``
     - Hilpert (cylinder)
     - 0.4 – 400,000
     - —
     - 1933
   * - ``external.pohlhausen_plate``
     - Pohlhausen (laminar flat plate)
     - Re ≤ 500,000
     - ≥ 0.6
     - 1921
   * - ``external.turbulent_plate``
     - Mixed Boundary Layer Flat Plate
     - Re ≥ 500,000
     - —
     - —

Correlation formulas
--------------------

**Churchill-Bernstein (1977)** — ``external.churchill_bernstein``

.. math::

   Nu = 0.3 + \frac{0.62\,Re^{1/2}\,Pr^{1/3}}
        {\left[1 + (0.4/Pr)^{2/3}\right]^{1/4}}
        \left[1 + \left(\frac{Re}{282{,}000}\right)^{5/8}\right]^{4/5}

Composite correlation valid for all :math:`Re` provided
:math:`Re \cdot Pr \geq 0.2`. Preferred all-Re correlation for cylinders in
crossflow.

**Žukauskas (1972)** — ``external.zukauskas_cylinder``

.. math::

   Nu = C\,Re^m\,Pr^{0.36}\,\left(\frac{Pr}{Pr_w}\right)^{0.25}

Tabular coefficients :math:`C` and :math:`m` are selected by :math:`Re` band.
The wall-Prandtl correction is omitted (set to 1) when
``fluid.wall_viscosity`` is not provided.

**Hilpert (1933)** — ``external.hilpert``

.. math::

   Nu = C\,Re^m\,Pr^{1/3}

Tabular coefficients from the original Hilpert table. Valid for
:math:`0.4 \leq Re < 400{,}000`.

**Pohlhausen (1921)** — ``external.pohlhausen_plate``

.. math::

   Nu_L = 0.664\,Re_L^{1/2}\,Pr^{1/3}

Exact similarity solution for a laminar boundary layer on an isothermal flat
plate. Valid for :math:`Re_L < 5 \times 10^5` and :math:`Pr \geq 0.6`.

**Mixed Boundary Layer Flat Plate** — ``external.turbulent_plate``

.. math::

   Nu_L = (0.037\,Re_L^{0.8} - 871)\,Pr^{1/3}

Accounts for the laminar leading-edge region assuming transition at
:math:`Re_{x,c} = 5 \times 10^5`. Valid for :math:`Re_L \geq 5 \times 10^5`.

Notes
-----

- ``external.churchill_bernstein`` is the preferred all-Re correlation for
  cylinders in crossflow.
- ``external.pohlhausen_plate`` and ``external.turbulent_plate`` together
  cover the full Re range for flat plates, with the transition at
  :math:`Re_L = 5 \times 10^5`.
- Characteristic length for plates is the plate length :math:`L`; for
  cylinders it is the outer diameter :math:`D`.
- For cylinders, ``external.hilpert`` is the older alternative to
  Churchill-Bernstein and does not include a Prandtl-ratio correction.

References
----------

Formulation (equations)
~~~~~~~~~~~~~~~~~~~~~~~

**Churchill-Bernstein (1977)**: Churchill, S.W. and Bernstein, M., "A correlating equation for
forced convection from gases and liquids to a circular cylinder in crossflow," *Journal of Heat
Transfer (ASME)*, vol. 99, no. 2, pp. 300–306, May 1977, DOI: 10.1115/1.3450685. Textbook:
Incropera, F.P., DeWitt, D.P., Bergman, T.L., and Lavine, A.S., *Fundamentals of Heat and Mass
Transfer*, 7th ed., Wiley, 2011, Sec. 7.4, Eq. 7.54, p. 432; Cengel, Y.A. and Ghajar, A.J.,
*Heat and Mass Transfer*, 5th ed., McGraw-Hill, 2015, Sec. 7-3, Eq. 7-35.

**Žukauskas (1972)**: Žukauskas, A., "Heat Transfer from Tubes in Crossflow," in *Advances in
Heat Transfer*, vol. 8, eds. Hartnett, J.P. and Irvine, T.F., Academic Press, New York,
pp. 93–160, 1972, DOI: 10.1016/S0065-2717(08)70038-8. Full volume PDF available (Internet
Archive, identifier AdvancesInHeatTransfer). Textbook: Incropera et al., 7th ed., Sec. 7.4,
Eq. 7.53, Table 7.4, p. 425.

**Hilpert (1933)**: Hilpert, R., "Wärmeabgabe von geheizten Drähten und Rohren im Luftstrom"
(Heat dissipation from heated wires and tubes in airflow), *Forschung auf dem Gebiete des
Ingenieurwesens*, vol. 4, no. 5, pp. 215–224, 1933, DOI: 10.1007/BF02719754. (German-language
original; Springer paywall.) The C and m tabular constants used here are the recalculated values
of Incropera et al., 7th ed., Sec. 7.4, Table 7.1, p. 421, which incorporate corrections from:
Fand, R.M. and Keswani, K.K., "Recalculation of some data of Hilpert for heat transfer from
cylinders in crossflow," *Journal of Heat Transfer (ASME)*, vol. 95, no. 2, p. 224, 1973,
DOI: 10.1115/1.3450030.

**Pohlhausen (1921)**: Pohlhausen, E., "Der Wärmeaustausch zwischen festen Körpern und
Flüssigkeiten mit kleiner Reibung und kleiner Wärmeleitung," *Zeitschrift für Angewandte
Mathematik und Mechanik (ZAMM)*, vol. 1, no. 2, pp. 115–121, 1921,
DOI: 10.1002/zamm.19210010205. (German-language original; PDF available from Zenodo record
1447401, licensed CC0.) Textbook: Incropera et al., 7th ed., Sec. 7.2, Eq. 7.30, p. 402;
Cengel & Ghajar, 5th ed., Sec. 7-1, Eq. 7-21.

**Mixed boundary layer flat plate (turbulent)**: This correlation is not attributable to a
single original paper. It combines the turbulent flat-plate result from the Colburn–Reynolds
analogy with a laminar leading-edge correction for transition at
:math:`Re_{x,c} = 5 \times 10^5`. Primary textbook source: Incropera et al., 7th ed.,
Sec. 7.2.3, Eq. 7.38, p. 407; Cengel & Ghajar, 5th ed., Sec. 7-2, Eq. 7-24. Theoretical
basis for the :math:`0.037\,Re^{0.8}` turbulent term: Schlichting, H., *Boundary Layer Theory*,
7th ed., McGraw-Hill, 1979, Ch. 21.

Variable definitions
~~~~~~~~~~~~~~~~~~~~

- :math:`Nu = h L / k` where :math:`L` is the characteristic length (cylinder: outer diameter
  :math:`D`; plate: length :math:`L`): Incropera et al., 7th ed., Secs. 7.2 and 7.4.
- :math:`Re = \rho u_\infty L / \mu` (free-stream Reynolds number): Incropera et al.,
  7th ed., Sec. 7.1.
- :math:`Pr = \mu c_p / k` (Prandtl number): Incropera et al., 7th ed., Sec. 7.1.
- :math:`Pr_w` (Prandtl number at wall/surface temperature, Žukauskas):
  Žukauskas (1972), pp. 93–160; Incropera et al., 7th ed., Table 7.4, p. 425.
- :math:`C`, :math:`m` (tabular coefficients, Žukauskas cylinder): Incropera et al., 7th ed.,
  Table 7.4, p. 425, sourced from Žukauskas (1972).
- :math:`C`, :math:`m` (tabular coefficients, Hilpert): Incropera et al., 7th ed.,
  Table 7.1, p. 421 (recalculated values incorporating Fand & Keswani 1973 corrections).
- Film temperature :math:`T_f = (T_s + T_\infty) / 2` (Churchill-Bernstein, Hilpert,
  Pohlhausen, turbulent plate property evaluation): Incropera et al., 7th ed., Secs. 7.2
  and 7.4.
- Free-stream temperature :math:`T_\infty` (property reference, Žukauskas):
  Žukauskas (1972); Incropera et al., 7th ed., Sec. 7.4, Table 7.4.

Range of applicability
~~~~~~~~~~~~~~~~~~~~~~

- **Churchill-Bernstein** all Re (0–4×10\ :sup:`7`), :math:`Re \cdot Pr \geq 0.2`:
  Churchill & Bernstein (1977), pp. 300–306; Incropera et al., 7th ed., Sec. 7.4,
  Eq. 7.54, p. 432.
- **Žukauskas (cylinder)** Re 1–1,000,000; Pr 0.7–500; properties at :math:`T_\infty`;
  :math:`Pr_w` at surface temperature:
  Incropera et al., 7th ed., Table 7.4, p. 425; Žukauskas (1972).
- **Hilpert** Re 0.4–400,000; Pr ≈ 0.7 (gases); properties at film temperature:
  Hilpert (1933); Incropera et al., 7th ed., Table 7.1, p. 421.
- **Pohlhausen** :math:`Re_L < 5 \times 10^5`; Pr ≥ 0.6; properties at film temperature:
  Incropera et al., 7th ed., Sec. 7.2, Eq. 7.30, p. 402.
- **Turbulent plate** :math:`Re_L \geq 5 \times 10^5`; Pr 0.6–60; properties at film
  temperature: Incropera et al., 7th ed., Sec. 7.2.3, Eq. 7.38, p. 407. Upper Re limit:
  YAML data records :math:`Re_{max} = 10^7`; Incropera Eq. 7.38 states validity up to
  :math:`10^8`. The page table does not show an upper bound; :math:`10^7` is documented
  in the correlation metadata.

Assumptions
~~~~~~~~~~~

- Isothermal cylinder in crossflow (Churchill-Bernstein, Žukauskas, Hilpert):
  Churchill & Bernstein (1977); Žukauskas (1972); Hilpert (1933); Incropera et al.,
  7th ed., Secs. 7.4.
- Properties at film temperature (Churchill-Bernstein, Hilpert, Pohlhausen, turbulent plate):
  Incropera et al., 7th ed., Secs. 7.2 and 7.4.
- Properties at free-stream temperature :math:`T_\infty`, with :math:`Pr_w` at wall
  temperature (Žukauskas): Žukauskas (1972); Incropera et al., 7th ed., Table 7.4.
- Isothermal flat plate, zero pressure gradient, Blasius velocity profile (Pohlhausen):
  Pohlhausen (1921); Incropera et al., 7th ed., Sec. 7.2.
- Mixed laminar–turbulent boundary layer with transition at :math:`Re_{x,c} = 5 \times 10^5`
  (turbulent plate): Incropera et al., 7th ed., Sec. 7.2.3, Eq. 7.38; Cengel & Ghajar,
  5th ed., Sec. 7-2.
- :math:`Pr^{1/3}` approximation valid for Pr ≥ 0.6 (Pohlhausen, Hilpert): Incropera et al.,
  7th ed., Secs. 7.2 and 7.4.

Uncertainty / error bounds
~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Churchill-Bernstein ±20%**: **UNCERTAIN** — the original paper (Churchill & Bernstein
  1977, pp. 300–306, reviewed during 2026-03-28 audit) does not state ±20%. Page 304
  characterizes Eq. (9) as "proposed as a lower bound for the computed and experimental
  values of :math:`\overline{Nu}_D`… for all Re and Pr such that :math:`Re\,Pr > 0.2`",
  noting that "data generally fall somewhat above equation (9)." No explicit ±% uncertainty
  bound appears anywhere in the paper. The ±20% is a textbook-attributed estimate
  (Incropera et al., 7th ed., Sec. 7.4).
- **Žukauskas (cylinder) ±25%**: textbook-attributed (Incropera 7th ed., Table 7.4, p. 425;
  Cengel & Ghajar 5th ed.). The primary source (Žukauskas 1972, "Heat Transfer from Tubes in
  Crossflow," *Advances in Heat Transfer*, Vol. 8, pp. 93–160) was reviewed in full during the 2026-03-28 audit; the single-cylinder
  correlation section (pp. 93–160) contains no explicit ±% uncertainty statement.
  **UNCERTAIN** — primary source reviewed; no explicit bound found.
- **Hilpert ±20%**: textbook-attributed. The Hilpert (1933) primary source is paywalled
  (Springer, DOI: 10.1007/BF02719754); no explicit ±% was identified in available
  excerpts. Note: the original Hilpert (1933) experimental data covered Re 2.1–231,000;
  the extended range Re 0.4–400,000 used here reflects the recalculated constants of
  Fand & Keswani (1973) as tabulated in Incropera et al., 7th ed., Table 7.1.
  **UNCERTAIN** — primary source not accessible.
- **Pohlhausen ±10%**: **UNCERTAIN** — the primary source (Pohlhausen 1921, ZAMM
  1(2):115–121, PDF available CC0) presents an analytical similarity solution only;
  no experimental scatter or ±% bound is stated. The ±10% is a textbook-consensus
  estimate for laminar flat-plate correlations.
- **Turbulent plate ±20%**: **UNCERTAIN** — this correlation has no single original
  paper. It is a standard textbook result combining the Colburn turbulent boundary layer
  formula with a laminar leading-edge correction (Incropera 7th ed. Sec. 7.2.3, Eq. 7.38,
  p. 407). No primary source states an explicit ±% bound.

Missing references
~~~~~~~~~~~~~~~~~~

None identified for this page. All equations and constants are traceable to sources listed
above (see flags under individual entries for items marked UNCERTAIN).

Traceability mapping
~~~~~~~~~~~~~~~~~~~~

- **Churchill-Bernstein equation (all constants: 0.3, 0.62, 0.4, 282,000, 5/8, 4/5)** →
  Churchill & Bernstein (1977), J. Heat Transfer 99(2):300–306, DOI: 10.1115/1.3450685;
  Incropera et al., 7th ed., Eq. 7.54, p. 432.
- **Churchill-Bernstein** :math:`Re \cdot Pr \geq 0.2` **criterion** → Churchill & Bernstein
  (1977), ibid.; Incropera et al., 7th ed., Sec. 7.4, p. 432.
- **Churchill-Bernstein Re range (0–4×10** :sup:`7` **)** → Churchill & Bernstein (1977),
  ibid.; Incropera et al., 7th ed., Sec. 7.4, p. 432.
- **Žukauskas cylinder equation form** :math:`C\,Re^m\,Pr^{0.36}\,(Pr/Pr_w)^{0.25}` →
  Žukauskas (1972), Adv. Heat Transfer 8:93–160, Eq. 33; Incropera et al., 7th ed., Eq. 7.53,
  Table 7.4, p. 425. **Flag: the Pr exponent shown on this page as 0.36 is a simplification.
  The primary source (Žukauskas 1972, Eq. 33) and Incropera Eq. 7.53 use n = 0.37 for
  Pr ≤ 10 and n = 0.36 for Pr > 10. The single-value exponent 0.36 understates the Pr
  sensitivity for fluids with Pr ≤ 10.**
- **Žukauskas cylinder C, m tabular coefficients** → Incropera et al., 7th ed., Table 7.4,
  p. 425, sourced from Žukauskas (1972). Verified against Žukauskas (1972) OCR extract:
  Re 1–40: C=0.75, m=0.4; Re 40–1,000: C=0.51, m=0.5; Re 1,000–200,000: C=0.26, m=0.6;
  Re 200,000–1,000,000: C=0.076, m=0.7.
- **Žukauskas cylinder Re 1–1,000,000; Pr 0.7–500** → Incropera et al., 7th ed., Table 7.4,
  p. 425; Žukauskas (1972).
- **Žukauskas cylinder** :math:`(Pr/Pr_w)^{0.25}` **correction** → Žukauskas (1972), Eq. 33
  (confirmed by OCR of Žukauskas 1972, *Advances in Heat Transfer*, Vol. 8); Incropera et al., 7th ed.,
  Eq. 7.53.
- **Hilpert equation form** :math:`C\,Re^m\,Pr^{1/3}` → Hilpert (1933), Forschung auf dem
  Gebiete des Ingenieurwesens 4(5):215–224; Incropera et al., 7th ed., Table 7.1, p. 421.
- **Hilpert C, m tabular coefficients (five Re bands)** → Incropera et al., 7th ed.,
  Table 7.1, p. 421 (recalculated per Fand & Keswani 1973, DOI: 10.1115/1.3450030).
  Note: the data YAML cites DOI 10.1007/BF02715487 for Hilpert (1933) while the references
  YAML cites DOI 10.1007/BF02719754. **Flag: these two DOIs differ; the correct DOI for
  Hilpert (1933) should be verified. Both are Springer BF-format DOIs for the same journal.**
- **Hilpert Re 0.4–400,000; properties at film temperature** → Hilpert (1933); Incropera
  et al., 7th ed., Table 7.1, p. 421.
- **Pohlhausen coefficient 0.664** → Pohlhausen (1921), ZAMM 1(2):115–121,
  DOI: 10.1002/zamm.19210010205 (PDF: Zenodo record 1447401, CC0); Incropera et al.,
  7th ed., Eq. 7.30, p. 402.
- **Pohlhausen** :math:`Re_L^{1/2}` **and** :math:`Pr^{1/3}` **exponents** → Pohlhausen (1921),
  ibid.; Incropera et al., 7th ed., Eq. 7.30.
- **Pohlhausen Re** :math:`< 5 \times 10^5`; **Pr ≥ 0.6** → Incropera et al., 7th ed.,
  Sec. 7.2, Eq. 7.30, p. 402.
- **Turbulent plate equation form** :math:`(0.037\,Re^{0.8} - 871)\,Pr^{1/3}` →
  Incropera et al., 7th ed., Sec. 7.2.3, Eq. 7.38, p. 407.
- **Turbulent plate coefficient 0.037** → Colburn–Reynolds analogy applied to turbulent
  flat plate; Schlichting (1979), Ch. 21; Incropera et al., 7th ed., Sec. 7.2.3.
- **Turbulent plate constant −871 (laminar leading-edge correction)** → derived from
  :math:`Re_{x,c} = 5 \times 10^5`: 871 = 0.037×(5×10\ :sup:`5`)\ :sup:`0.8` −
  0.664×(5×10\ :sup:`5`)\ :sup:`0.5`; Incropera et al., 7th ed., Sec. 7.2.3, Eq. 7.38.
- **Turbulent plate transition at** :math:`Re_{x,c} = 5 \times 10^5` → Incropera et al.,
  7th ed., Sec. 7.2.3; Cengel & Ghajar, 5th ed., Sec. 7-2.
- **Turbulent plate Re** :math:`\geq 5 \times 10^5`; **Pr 0.6–60** → Incropera et al.,
  7th ed., Sec. 7.2.3, Eq. 7.38, p. 407; Cengel & Ghajar, 5th ed., Eq. 7-24.
- **Properties at film temperature (Churchill-Bernstein, Hilpert, Pohlhausen, turbulent
  plate)** → Incropera et al., 7th ed., Secs. 7.2 and 7.4.
- **Churchill-Bernstein uncertainty ±20%** → **UNCERTAIN** — not stated in the original
  paper (Churchill & Bernstein 1977, pp. 300–306, reviewed 2026-03-28). The paper
  characterizes Eq. (9) as a lower bound (p. 304); no ±% appears. Textbook attribution
  only (Incropera et al., 7th ed., Sec. 7.4).
- **Žukauskas uncertainty ±25%** → **UNCERTAIN** (specific page not identified).
- **Hilpert uncertainty ±20%** → **UNCERTAIN** (specific page not identified).
- **Pohlhausen uncertainty ±10%** → **UNCERTAIN** (typical estimate; specific page not
  identified).
- **Turbulent plate uncertainty ±20%** → **UNCERTAIN** (specific page not identified).
