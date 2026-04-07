"""Evaluate page — main htcie interface."""

from __future__ import annotations

from nicegui import ui

from htcie.core.loader import build_registry
from htcie.core.pipeline import run_evaluation
from htcie.core.registry import CorrelationRegistry
from htcie.core.state import (
    BoundaryConditions,
    EngineeringState,
    FlowState,
    FluidProperties,
    Geometry,
)
from htcie.reports.renderer import render_html
from htcie.reports.schema import HtcieReport


_registry: CorrelationRegistry | None = None


def _get_registry() -> CorrelationRegistry:
    global _registry
    if _registry is None:
        _registry = build_registry()
    return _registry


def _run_evaluation(
    density: float,
    viscosity: float,
    thermal_conductivity: float,
    heat_capacity: float,
    geometry_type: str,
    characteristic_length: float,
    hydraulic_diameter: float | None,
    boundary_type: str,
    velocity: float,
    wall_viscosity: float | None = None,
    developing_length: float | None = None,
) -> HtcieReport | None:
    """Run the full evaluation pipeline and return an HtcieReport."""
    fluid = FluidProperties(
        density=density,
        viscosity=viscosity,
        thermal_conductivity=thermal_conductivity,
        heat_capacity=heat_capacity,
        wall_viscosity=wall_viscosity,
    )
    geom = Geometry(
        geometry_type=geometry_type,
        characteristic_length=characteristic_length,
        hydraulic_diameter=hydraulic_diameter or characteristic_length,
    )
    boundary = BoundaryConditions(boundary_type=boundary_type)
    flow = FlowState(velocity=velocity, developing_length=developing_length)
    state = EngineeringState(fluid=fluid, geometry=geom, boundary=boundary, flow=flow)
    return run_evaluation(state, _get_registry())


def setup() -> None:
    """Register the evaluate page."""

    @ui.page("/")
    def evaluate_page() -> None:
        last_report: list[HtcieReport] = []  # mutable container for closure

        ui.add_head_html(
            "<style>"
            ".q-tooltip { font-size: 0.85rem !important;"
            " padding: 8px 12px !important; max-width: 320px; }"
            "</style>"
            "<script>window.MathJax = {tex: {inlineMath: [['$', '$']]}};</script>"
            '<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"'
            ' id="MathJax-script" async></script>'
        )

        ui.label("htcie — Heat Transfer Correlation Intelligence Engine").classes(
            "text-2xl font-bold"
        )

        with ui.row().classes("w-full gap-4 items-start"):
            with ui.card().classes("flex-1 min-w-0"):
                ui.label("Engineering State Input").classes(
                    "text-lg font-semibold mb-2"
                )

                # ── Fluid Properties ──────────────────────────────────────────
                with ui.card().classes("w-full bg-blue-50 rounded-lg p-2"):
                    ui.label("Fluid Properties").classes(
                        "font-semibold text-sm text-blue-900 mb-0"
                    )
                    with ui.column().classes("w-full pl-2 gap-1"):
                        density_input = (
                            ui.number("Density [kg/m³]", value=1000.0, min=0.001)
                            .classes("w-full")
                            .props('title="" :input-attrs="{title: \'\'}"')
                            .tooltip(
                                "ρ — Fluid density. Mass per unit volume. [kg/m³]."
                                " Typical: water 998, air 1.2."
                            )
                        )
                        viscosity_input = (
                            ui.number(
                                "Viscosity [Pa·s]",
                                value=0.001,
                                min=1e-10,
                                format="%.6f",
                            )
                            .classes("w-full")
                            .props('title="" :input-attrs="{title: \'\'}"')
                            .tooltip(
                                "μ — Dynamic viscosity. Fluid resistance to shear"
                                " flow. [Pa·s]. Typical: water 0.001,"
                                " air 1.8×10⁻⁵."
                            )
                        )
                        k_input = (
                            ui.number(
                                "Thermal conductivity [W/m·K]",
                                value=0.6,
                                min=0.001,
                            )
                            .classes("w-full")
                            .props('title="" :input-attrs="{title: \'\'}"')
                            .tooltip(
                                "k — Thermal conductivity. Rate of heat conduction"
                                " through the fluid. [W/m·K]. Typical: water 0.6,"
                                " air 0.026."
                            )
                        )
                        cp_input = (
                            ui.number("Heat capacity [J/kg·K]", value=4180.0, min=0.001)
                            .classes("w-full")
                            .props('title="" :input-attrs="{title: \'\'}"')
                            .tooltip(
                                "cp — Specific heat capacity. Energy required to"
                                " raise 1 kg by 1 K. [J/kg·K]. Typical: water"
                                " 4180, air 1005."
                            )
                        )

                ui.separator().classes("my-1")

                # ── Geometry ──────────────────────────────────────────────────
                with ui.card().classes("w-full bg-blue-50 rounded-lg p-2"):
                    ui.label("Geometry").classes(
                        "font-semibold text-sm text-blue-900 mb-0"
                    )
                    with ui.column().classes("w-full pl-2 gap-1"):
                        geo_type = (
                            ui.select(
                                {
                                    "circular_tube": "Circular tube",
                                    "cylinder_crossflow": "Cylinder crossflow",
                                    "flat_plate": "Flat plate",
                                },
                                value="circular_tube",
                                label="Geometry type",
                            )
                            .classes("w-full")
                            .tooltip(
                                "Geometry that defines the convection problem."
                                " Determines which correlations are applicable."
                            )
                        )
                        char_len = (
                            ui.number(
                                "Characteristic length [m]",
                                value=0.025,
                                min=1e-6,
                                format="%.4f",
                            )
                            .classes("w-full")
                            .props('title="" :input-attrs="{title: \'\'}"')
                            .tooltip(
                                "L — Characteristic length. Length scale for Re and"
                                " Nu. Tube: inner diameter; plate: length; cylinder:"
                                " outer diameter. [m]."
                            )
                        )
                        hyd_dia = (
                            ui.number(
                                "Hydraulic diameter [m]",
                                value=0.025,
                                min=1e-6,
                                format="%.4f",
                            )
                            .classes("w-full")
                            .props('title="" :input-attrs="{title: \'\'}"')
                            .tooltip(
                                "Dh — Hydraulic diameter. 4A/P for non-circular"
                                " sections; equals inner diameter for circular"
                                " tubes. [m]."
                            )
                        )

                ui.separator().classes("my-1")

                # ── Boundary Conditions ───────────────────────────────────────
                with ui.card().classes("w-full bg-blue-50 rounded-lg p-2"):
                    ui.label("Boundary Conditions").classes(
                        "font-semibold text-sm text-blue-900 mb-0"
                    )
                    with ui.column().classes("w-full pl-2 gap-1"):
                        bc_type = (
                            ui.select(
                                {
                                    "constant_wall_temperature": (
                                        "Constant wall temperature"
                                    ),
                                    "constant_heat_flux": "Constant heat flux",
                                },
                                value="constant_wall_temperature",
                                label="Boundary type",
                            )
                            .classes("w-full")
                            .tooltip(
                                "Thermal boundary condition at the wall. Affects the"
                                " Nusselt number coefficient in many correlations."
                            )
                        )

                ui.separator().classes("my-1")

                # ── Flow ──────────────────────────────────────────────────────
                with ui.card().classes("w-full bg-blue-50 rounded-lg p-2"):
                    ui.label("Flow").classes("font-semibold text-sm text-blue-900 mb-0")
                    with ui.column().classes("w-full pl-2 gap-1"):
                        velocity_input = (
                            ui.number(
                                "Velocity [m/s]",
                                value=0.4,
                                min=1e-6,
                                format="%.4f",
                            )
                            .classes("w-full")
                            .props('title="" :input-attrs="{title: \'\'}"')
                            .tooltip(
                                "u — Mean flow velocity. Bulk velocity used to"
                                " compute the Reynolds number. [m/s]. Typical:"
                                " 0.1–10 m/s for liquid; 1–50 m/s for gas."
                            )
                        )

                def handle_evaluate() -> None:
                    result_container.clear()
                    try:
                        report = _run_evaluation(
                            density=float(density_input.value),
                            viscosity=float(viscosity_input.value),
                            thermal_conductivity=float(k_input.value),
                            heat_capacity=float(cp_input.value),
                            geometry_type=str(geo_type.value),
                            characteristic_length=float(char_len.value),
                            hydraulic_diameter=float(hyd_dia.value),
                            boundary_type=str(bc_type.value),
                            velocity=float(velocity_input.value),
                        )
                        if report is None:
                            with result_container:
                                ui.label("No applicable methods found.").classes(
                                    "text-yellow-600"
                                )
                            return
                        last_report.clear()
                        last_report.append(report)
                        save_btn.enable()
                        with result_container:
                            from htcie.gui.components.results_panel import (
                                render_results,
                            )

                            render_results(report.to_dict())
                        ui.run_javascript(
                            "setTimeout(()=>{"
                            " if(window.MathJax) MathJax.typesetPromise()"
                            "}, 500)"
                        )
                    except Exception as exc:
                        with result_container:
                            ui.label(f"Error: {exc}").classes("text-red-500")

                def handle_save_html() -> None:
                    if not last_report:
                        return
                    report = last_report[0]
                    data = report.to_dict()
                    charts = None
                    if data.get("ranking") and data.get("evaluations"):
                        import plotly.io as pio

                        from htcie.gui.components.charts import (
                            build_ranking_lollipop,
                            build_uncertainty_lollipop,
                        )

                        charts = {
                            "ranking": pio.to_html(
                                build_ranking_lollipop(data["ranking"]),
                                full_html=False,
                                include_plotlyjs=True,
                            ),
                            "uncertainty": pio.to_html(
                                build_uncertainty_lollipop(
                                    data["evaluations"], data["ranking"]
                                ),
                                full_html=False,
                                include_plotlyjs=False,
                            ),
                        }
                    html_bytes = render_html(report, charts=charts).encode("utf-8")
                    timestamp = report.timestamp.replace(", ", "_").replace(":", "-").replace(" ", "_")
                    ui.download(html_bytes, filename=f"htcie_report_{timestamp}.html")

                with ui.row().classes("gap-2 mt-4"):
                    ui.button("Evaluate", on_click=handle_evaluate)
                    save_btn = ui.button(
                        "Save as HTML", on_click=handle_save_html
                    ).props("outline")
                    save_btn.disable()

            with ui.card().classes("flex-3 min-w-0 overflow-hidden"):
                ui.label("Results").classes("text-lg font-semibold")
                result_container = ui.column().classes("w-full")
