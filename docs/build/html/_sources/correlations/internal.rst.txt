Internal Forced Convection
==========================

Six correlations for internal forced convection in circular tubes.
All correlations output the Nusselt number :math:`Nu = h D / k`.

.. list-table::
   :header-rows: 1
   :widths: 28 30 22 10 10

   * - Key
     - Title
     - Re Range
     - Pr Range
     - Year
   * - ``internal.gnielinski``
     - Gnielinski
     - 3,000 – 5,000,000
     - 0.5 – 2,000
     - 1976
   * - ``internal.petukhov``
     - Petukhov
     - 10,000 – 5,000,000
     - 0.5 – 2,000
     - 1970
   * - ``internal.dittus_boelter``
     - Dittus-Boelter
     - 10,000 – 120,000
     - 0.6 – 160
     - 1930
   * - ``internal.sieder_tate``
     - Sieder-Tate
     - 10,000 – 1,000,000
     - —
     - 1936
   * - ``internal.shah_laminar``
     - Shah (laminar)
     - Re ≤ 2,300
     - —
     - 1978
   * - ``internal.churchill_ozoe``
     - Churchill-Ozoe (laminar)
     - Re ≤ 2,300
     - —
     - 1973

Correlation formulas
--------------------

**Gnielinski (1976)** — ``internal.gnielinski``

.. math::

   Nu = \frac{(f/8)(Re - 1000)\,Pr}
        {1 + 12.7\sqrt{f/8}\,(Pr^{2/3} - 1)}

where :math:`f = (0.790 \ln Re - 1.64)^{-2}` (Petukhov friction factor).
Preferred correlation for transitional and turbulent flow.
Literature uncertainty ≈ 10 %.

**Petukhov (1970)** — ``internal.petukhov``

.. math::

   Nu = \frac{(f/8)\,Re\,Pr}
        {1.07 + 12.7\sqrt{f/8}\,(Pr^{2/3} - 1)}

Uses the same friction factor as Gnielinski. Valid for fully turbulent smooth
tubes (:math:`Re \geq 10{,}000`). Literature uncertainty: ±5–6% for Pr 0.5–200;
±10% for Pr 0.5–2,000 (primary source confirmed, Petukhov 1970 p. 523).

**Dittus-Boelter (1930)** — ``internal.dittus_boelter``

.. math::

   Nu = 0.023\,Re^{0.8}\,Pr^n, \quad
   n = \begin{cases} 0.4 & T_w > T_b \\ 0.3 & T_w < T_b \end{cases}

Classic turbulent correlation. Literature uncertainty ≈ 25 %.

**Sieder-Tate (1936)** — ``internal.sieder_tate``

.. math::

   Nu = 0.027\,Re^{0.8}\,Pr^{1/3}\,\left(\frac{\mu}{\mu_w}\right)^{0.14}

The viscosity-ratio correction :math:`(\mu/\mu_w)^{0.14}` is applied when
``fluid.wall_viscosity`` is provided; omitted otherwise.

**Shah (1978)** — ``internal.shah_laminar``

.. math::

   Nu = 3.66 + \frac{0.0668\,Gz}{1 + 0.04\,Gz^{2/3}},
   \quad Gz = Re \cdot Pr \cdot \frac{D_h}{L}

Thermally-developing laminar flow with a constant-wall-temperature base.
Falls back to :math:`Nu = 3.66` when ``developing_length`` is absent.

**Churchill-Ozoe (1973)** — ``internal.churchill_ozoe``

.. math::

   Nu = Nu_0 + \frac{0.0668\,Gz}{1 + 0.04\,Gz^{2/3}}

where :math:`Nu_0 = 3.66` (UWT) or :math:`Nu_0 = 4.36` (UHF).
Falls back to :math:`Nu_0` when ``developing_length`` is absent.

Notes
-----

- ``internal.gnielinski`` is preferred for transitional and turbulent regimes
  (Re 3,000 – 5,000,000) due to its lower literature uncertainty.
- ``internal.petukhov`` is valid for smooth-tube turbulent flow (Re ≥ 10,000).
- ``internal.shah_laminar`` and ``internal.churchill_ozoe`` apply to
  thermally developing or fully developed laminar flow; ``churchill_ozoe``
  additionally selects the correct fully-developed base according to the
  boundary-condition type.
- ``internal.sieder_tate`` is included for legacy compatibility; Gnielinski
  is preferred when wall-viscosity data is not available.
- All turbulent correlations assume a smooth, straight circular tube with
  constant fluid properties evaluated at bulk temperature.

References
----------

Formulation (equations)
~~~~~~~~~~~~~~~~~~~~~~~

**Gnielinski (1976)**: Gnielinski, V., "New equations for heat and mass transfer in turbulent
pipe and channel flow," *International Chemical Engineering*, vol. 16, no. 2, pp. 359–368, 1976.
English translation of: Gnielinski, V., *Forschung im Ingenieurwesen*, vol. 41, no. 1, pp. 8–16,
1975, DOI: 10.1007/BF02559682. Textbook presentation: Incropera, F.P., DeWitt, D.P., Bergman, T.L.,
and Lavine, A.S., *Fundamentals of Heat and Mass Transfer*, 7th ed., Wiley, 2011, Sec. 8.5,
Eq. 8.62, p. 514.

**Petukhov (1970)**: Petukhov, B.S., "Heat Transfer and Friction in Turbulent Pipe Flow with
Variable Physical Properties," in *Advances in Heat Transfer*, vol. 6, eds. Hartnett, J.P. and
Irvine, T.F., Academic Press, New York, pp. 503–564, 1970, DOI: 10.1016/S0065-2717(08)70153-9.
Textbook: Incropera et al., 7th ed., Sec. 8.5, Eq. 8.63.

**Dittus-Boelter (1930)**: Dittus, F.W. and Boelter, L.M.K., "Heat Transfer in Automobile
Radiators of the Tubular Type," *University of California Publications in Engineering*, vol. 2,
no. 13, pp. 443–461, 1930. Reprint: *International Communications in Heat and Mass Transfer*,
vol. 12, no. 1, pp. 3–22, 1985, DOI: 10.1016/0735-1933(85)90003-X. Textbook: Incropera et al.,
7th ed., Sec. 8.5, Eq. 8.60, p. 514; Cengel, Y.A. and Ghajar, A.J., *Heat and Mass Transfer*,
5th ed., McGraw-Hill, 2015, Sec. 8-4, Eq. 8-55.

**Sieder-Tate (1936)**: Sieder, E.N. and Tate, G.E., "Heat Transfer and Pressure Drop of Liquids
in Tubes," *Industrial & Engineering Chemistry*, vol. 28, no. 12, pp. 1429–1435, 1936,
DOI: 10.1021/ie50324a027. Textbook: Incropera et al., 7th ed., Sec. 8.5, Eq. 8.61;
Cengel & Ghajar, 5th ed., Sec. 8-4, Eq. 8-56.

**Shah (1978)**: Shah, R.K. and London, A.L., *Laminar Flow Forced Convection in Ducts: A Source
Book for Compact Heat Exchanger Analytical Data*, Supplement 1 to *Advances in Heat Transfer*,
eds. Irvine, T.F. and Hartnett, J.P., Academic Press, New York, 1978, Ch. 5, ISBN: 978-0-12-020051-1.
Textbook: Incropera et al., 7th ed., Sec. 8.4, Eq. 8.58; Cengel & Ghajar, 5th ed., Sec. 8-3.

  **Note on formula origin**: The entry-length formula
  :math:`Nu = 3.66 + 0.0668\,Gz\,/\,(1 + 0.04\,Gz^{2/3})` was originally proposed by
  Hausen (1943) and was tabulated and validated by Shah & London (1978). A full citation
  for Hausen (1943) is not available in the project reference set — see
  **Missing References** below.

**Churchill-Ozoe (1973)**:

- UHF boundary condition: Churchill, S.W. and Ozoe, H., "Correlations for laminar forced
  convection with uniform heating in flow over a plate and in developing and fully developed
  flow in a tube," *Journal of Heat Transfer (ASME)*, vol. 95, no. 1, pp. 78–84, Feb. 1973,
  DOI: 10.1115/1.3450009.
- UWT boundary condition: Churchill, S.W. and Ozoe, H., "Correlations for laminar forced
  convection in flow over an isothermal flat plate and in developing and fully developed flow
  in an isothermal tube," *Journal of Heat Transfer (ASME)*, vol. 95, no. 3, pp. 416–419,
  Aug. 1973, DOI: 10.1115/1.3450078.
- Textbook: Incropera et al., 7th ed., Sec. 8.4, Eq. 8.57.

Variable definitions
~~~~~~~~~~~~~~~~~~~~

- :math:`Nu = h D / k` (Nusselt number for circular tube of diameter :math:`D`):
  Incropera et al., 7th ed., Sec. 8.1.
- :math:`Re = \rho u_m D / \mu` (bulk-velocity Reynolds number):
  Incropera et al., 7th ed., Sec. 8.1.
- :math:`Pr = \mu c_p / k` (Prandtl number): Incropera et al., 7th ed., Sec. 8.1.
- :math:`f = (0.790 \ln Re - 1.64)^{-2}` (Petukhov smooth-pipe friction factor):
  Petukhov (1970), pp. 503–564; Incropera et al., 7th ed., Eq. 8.21.
- :math:`Gz = Re \cdot Pr \cdot D / L` (Graetz number): Shah & London (1978), Ch. 5;
  Incropera et al., 7th ed., Sec. 8.4, Eq. 8.58.
- :math:`\mu_w` (dynamic viscosity at wall temperature, Sieder-Tate only):
  Sieder & Tate (1936), p. 1429; Incropera et al., 7th ed., Eq. 8.61.
- :math:`Nu_0 = 3.66` (fully developed Nu for constant wall temperature):
  exact Graetz-problem solution, Incropera et al., 7th ed., Sec. 8.4, Table 8.1.
- :math:`Nu_0 = 4.36` (fully developed Nu for uniform heat flux):
  exact solution, Incropera et al., 7th ed., Sec. 8.4, Table 8.1.

Range of applicability
~~~~~~~~~~~~~~~~~~~~~~

- **Gnielinski** Re 3,000–5,000,000; Pr 0.5–2,000; L/D ≥ 10:
  Incropera et al., 7th ed., Sec. 8.5, Eq. 8.62, p. 514.
- **Petukhov** Re 10,000–5,000,000; Pr 0.5–2,000:
  Petukhov (1970), pp. 503–564; Incropera et al., 7th ed., Sec. 8.5, Eq. 8.63.
- **Dittus-Boelter** Re 10,000–120,000; Pr 0.6–160; L/D ≥ 10:
  Incropera et al., 7th ed., Sec. 8.5, Eq. 8.60, p. 514. The Re upper bound of 120,000
  reflects the McAdams (1954) form of the correlation; Incropera Eq. 8.60 states Re ≥ 10,000
  with no explicit upper bound. The Pr lower bound of 0.6 is from Incropera 7th ed.;
  some earlier sources and the original 1930 publication used Pr_min = 0.7.
- **Sieder-Tate** Re ≥ 10,000; Pr 0.7–16,700; L/D ≥ 10:
  Incropera et al., 7th ed., Sec. 8.5, Eq. 8.61.
  Note: the summary table on this page shows "—" for the Pr range, which omits the
  documented range of 0.7–16,700 from Incropera Eq. 8.61.
- **Shah** Re ≤ 2,300 (laminar), all Pr, with fallback to Nu = 3.66 for fully developed
  limit (Gz → 0): Incropera et al., 7th ed., Sec. 8.4, Eq. 8.58.
- **Churchill-Ozoe** Re ≤ 2,300 (laminar):
  Incropera et al., 7th ed., Sec. 8.4, Eq. 8.57.

Assumptions
~~~~~~~~~~~

- Smooth, straight circular tube (Gnielinski, Petukhov, Dittus-Boelter, Sieder-Tate):
  Gnielinski (1976); Petukhov (1970); Incropera et al., 7th ed., Sec. 8.5.
- Fluid properties at bulk mean temperature (Gnielinski, Petukhov, Dittus-Boelter, Shah,
  Churchill-Ozoe): Incropera et al., 7th ed., Sec. 8.5 (turbulent) and Sec. 8.4 (laminar).
- Wall viscosity :math:`\mu_w` evaluated at wall temperature (Sieder-Tate only):
  Sieder & Tate (1936); Incropera et al., 7th ed., Eq. 8.61.
- Thermally developing, hydrodynamically fully developed flow (Shah, Churchill-Ozoe):
  Shah & London (1978), Ch. 5; Churchill & Ozoe (1973).
- Constant wall temperature (UWT) boundary condition for Shah: Shah & London (1978), Ch. 5.
- Boundary-condition type selectable between UWT and UHF for Churchill-Ozoe:
  Churchill & Ozoe (1973), DOI: 10.1115/1.3450009 (UHF) and DOI: 10.1115/1.3450078 (UWT).

Uncertainty / error bounds
~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Gnielinski ±10%**: **UNCERTAIN** regarding original paper. The 1976 original paper
  (Gnielinski 1976, Int. Chem. Eng. 16(2):359–368) is not available in any accessible
  digital form and could not be verified. The available 2013 update (Gnielinski, IJHMT
  63:134–140, reviewed during 2026-03-28 audit) does not restate a ±10% bound explicitly.
  The ±10% is sourced from Cengel & Ghajar, 5th ed., Sec. 8-5.
- **Petukhov**: The primary source (Petukhov 1970, p. 523) states the accuracy in two
  parts: **±5–6%** for Re 10,000–5,000,000 and **Pr 0.5–200**; **±10%** for the wider
  range Pr 0.5–2,000. These are the only directly verified uncertainty bounds in the
  catalog. Source: Petukhov (1970), Adv. Heat Transfer 6:503–564, p. 523, Eq. (50).
- **Dittus-Boelter ±25%**: textbook-attributed (Incropera et al. Eq. 8.60; Cengel &
  Ghajar Eq. 8-55). The original 1930 publication (UC Pubs. Eng. 2(13):443–461) is
  unavailable; the 1985 reprint (ICHMT 12:3–22, DOI: 10.1016/0735-1933(85)90003-X)
  is paywalled. Cannot verify against primary source. **UNCERTAIN.**
- **Sieder-Tate ±20%**: textbook-attributed. The original paper (Sieder & Tate 1936,
  Ind. Eng. Chem. 28:1429–1435, Table II, p. 1433, reviewed during 2026-03-28 audit)
  shows deviations ranging from ±4% to ±63% by fluid type and Re range. No single
  ±20% bound is stated anywhere in the paper. The ±20% is a textbook-consensus estimate.
  **UNCERTAIN.**
- **Shah ±10%**: textbook-consensus estimate. The original conference paper (Shah 1978,
  Proc. National HMT Conference, IIT Bombay) is not available in any accessible digital
  form. Cannot verify. **UNCERTAIN.**
- **Churchill-Ozoe ±10%**: textbook-consensus estimate. The original papers (Churchill &
  Ozoe 1973, J. Heat Transfer 95:78–84 and 95:416–419) are paywalled (ASME). Cannot
  verify. **UNCERTAIN.**

Missing references
~~~~~~~~~~~~~~~~~~

- **Hausen (1943)**: the entry-length formula used by both Shah (1978) and Churchill-Ozoe
  was originally proposed by Hausen. Full citation: Hausen, H., "Darstellung des
  Wärmeüberganges in Rohren durch verallgemeinerte Potenzbeziehungen," *Z. VDI Beih.
  Verfahrenstechnik*, vol. 4, pp. 91–98, 1943. This source is not available in the
  project reference set; the formula is accessed through Shah & London (1978) and
  Incropera et al., 7th ed., Sec. 8.4, Eq. 8.58.

Traceability mapping
~~~~~~~~~~~~~~~~~~~~

- **Gnielinski equation form** → Gnielinski (1976), Int. Chem. Eng. 16(2):359–368;
  Incropera et al., 7th ed., Eq. 8.62, p. 514.
- **Petukhov equation (denominator constant 1.07)** → Petukhov (1970), Adv. Heat Transfer
  6:503–564, DOI: 10.1016/S0065-2717(08)70153-9; Incropera et al., 7th ed., Eq. 8.63.
- **Friction factor** :math:`f = (0.790 \ln Re - 1.64)^{-2}` → Petukhov (1970), ibid.;
  Incropera et al., 7th ed., Eq. 8.21.
- **Dittus-Boelter coefficients (0.023, exponent 0.8)** → Dittus & Boelter (1930), UC Pubs.
  Eng. 2(13):443–461; 1985 reprint DOI: 10.1016/0735-1933(85)90003-X; Incropera et al.,
  7th ed., Eq. 8.60, p. 514.
- **Dittus-Boelter exponent** :math:`n = 0.4` **(heating) /** :math:`0.3` **(cooling)** →
  Dittus & Boelter (1930); Incropera et al., 7th ed., Eq. 8.60, p. 514.
- **Sieder-Tate coefficients (0.027, 0.8, 1/3) and viscosity exponent (0.14)** →
  Sieder & Tate (1936), Ind. Eng. Chem. 28(12):1429–1435, DOI: 10.1021/ie50324a027;
  Incropera et al., 7th ed., Eq. 8.61.
- **Shah equation coefficients (0.0668, 0.04)** → Shah & London (1978), Ch. 5;
  Incropera et al., 7th ed., Eq. 8.58. Original proposal by Hausen (1943) —
  **MISSING REFERENCE** (see above).
- **Churchill-Ozoe equation coefficients (0.0668, 0.04)** → Churchill & Ozoe (1973),
  J. Heat Transfer 95(1):78–84, DOI: 10.1115/1.3450009; companion: 95(3):416–419,
  DOI: 10.1115/1.3450078; Incropera et al., 7th ed., Eq. 8.57.
- :math:`Nu_0 = 3.66` **(UWT fully developed base)** → Incropera et al., 7th ed.,
  Sec. 8.4, Table 8.1.
- :math:`Nu_0 = 4.36` **(UHF fully developed base)** → Incropera et al., 7th ed.,
  Sec. 8.4, Table 8.1.
- **Graetz number definition** :math:`Gz = Re \cdot Pr \cdot D / L` → Shah & London (1978),
  Ch. 5; Incropera et al., 7th ed., Sec. 8.4, Eq. 8.58.
- **Gnielinski Re 3,000–5,000,000; Pr 0.5–2,000; L/D ≥ 10** → Incropera et al., 7th ed.,
  Sec. 8.5, p. 514.
- **Petukhov Re 10,000–5,000,000; Pr 0.5–2,000** → Petukhov (1970), p. 503;
  Incropera et al., 7th ed., Sec. 8.5, Eq. 8.63.
- **Dittus-Boelter Re 10,000–120,000; Pr 0.6–160; L/D ≥ 10** → Incropera et al., 7th ed.,
  Sec. 8.5, Eq. 8.60, p. 514.
- **Sieder-Tate Re ≥ 10,000; Pr 0.7–16,700; L/D ≥ 10** → Incropera et al., 7th ed.,
  Sec. 8.5, Eq. 8.61.
- **Shah Re ≤ 2,300** → Incropera et al., 7th ed., Sec. 8.4, Eq. 8.58.
- **Churchill-Ozoe Re ≤ 2,300** → Incropera et al., 7th ed., Sec. 8.4, Eq. 8.57.
- **Smooth-tube assumption (all turbulent correlations)** → Petukhov (1970); Gnielinski
  (1976); Incropera et al., 7th ed., Sec. 8.5.
- **Properties at bulk mean temperature (turbulent)** → Incropera et al., 7th ed., Sec. 8.5.
- **Wall viscosity** :math:`\mu_w` **at wall temperature (Sieder-Tate)** → Sieder & Tate
  (1936), p. 1429; Incropera et al., 7th ed., Eq. 8.61.
- **UWT/UHF boundary condition switching (Churchill-Ozoe)** → Churchill & Ozoe (1973),
  DOI: 10.1115/1.3450009 and DOI: 10.1115/1.3450078.
- **Gnielinski uncertainty ±10%** → Cengel & Ghajar, 5th ed., Sec. 8-5. **UNCERTAIN**
  regarding primary source: Gnielinski (1976) is inaccessible; the available 2013 update
  (IJHMT 63:134–140, reviewed 2026-03-28) does not restate this value.
- **Petukhov uncertainty ±5–6% (Pr 0.5–200) / ±10% (Pr 0.5–2,000)** → Petukhov (1970),
  Adv. Heat Transfer 6:503–564, p. 523, Eq. (50). Primary source confirmed. This is the
  only uncertainty bound in the catalog verified directly from an accessible primary source.
- **Dittus-Boelter uncertainty ±25%** → textbook attribution only (Incropera Eq. 8.60;
  Cengel Eq. 8-55). Primary source not accessible. **UNCERTAIN.**
- **Sieder-Tate uncertainty ±20%** → textbook-consensus estimate. Primary source (Sieder
  & Tate 1936, Table II, p. 1433, reviewed 2026-03-28) shows deviations ±4–63% by
  fluid/regime; no single ±20% stated. **UNCERTAIN.**
- **Shah uncertainty ±10%** → textbook-consensus. Primary source (Shah 1978 conference
  paper) not accessible digitally. **UNCERTAIN.**
- **Churchill-Ozoe uncertainty ±10%** → textbook-consensus. Primary sources paywalled
  (ASME). **UNCERTAIN.**
