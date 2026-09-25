"""Phase 8 preliminary spacecraft configuration and CAD-ready geometry.

The generated STL and drawings communicate the concept envelope and layout.
They are not manufacturing geometry, structural substantiation or released CAD.
"""

from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from spacecraft_subsystems import evaluate_subsystems


BUS_DIMS_M = (0.70, 0.70, 0.90)
SOLAR_WING_DIMS_M = (0.75, 0.50, 0.015)
SOLAR_WING_COUNT = 2
SELECTED_SOLAR_AREA_M2 = SOLAR_WING_DIMS_M[0] * SOLAR_WING_DIMS_M[1] * SOLAR_WING_COUNT
SELECTED_RADIATOR_AREA_M2 = 0.60


@dataclass(frozen=True)
class Component:
    name: str
    mass_kg: float
    x_m: float
    y_m: float
    z_m: float
    size_x_m: float
    size_y_m: float
    size_z_m: float
    category: str = "equipment"


COMPONENTS = (
    Component("Payload telescope", 7.932, 0.00, 0.00, -0.08, 0.24, 0.24, 0.65, "payload"),
    Component("Structure and mechanisms", 10.0, 0.00, 0.00, 0.00, 0.70, 0.70, 0.90, "distributed"),
    Component("Electrical power system", 7.0, 0.18, 0.15, 0.12, 0.22, 0.18, 0.14),
    Component("ADCS assembly", 6.0, -0.18, -0.15, 0.10, 0.22, 0.22, 0.18),
    Component("X-band communications", 4.0, 0.18, -0.16, 0.15, 0.22, 0.16, 0.12),
    Component("Command and data handling", 2.0, -0.18, 0.16, 0.15, 0.20, 0.16, 0.10),
    Component("Thermal hardware", 4.0, 0.00, 0.00, 0.00, 0.65, 0.02, 0.46, "distributed"),
    Component("Propulsion hardware", 3.5, -0.24, 0.00, -0.18, 0.14, 0.16, 0.18),
    Component("Harness and integration", 2.5, 0.00, 0.00, 0.00, 0.60, 0.60, 0.70, "distributed"),
    Component("Propellant", 1.3201610641, -0.24, 0.00, -0.18, 0.12, 0.12, 0.14, "contained"),
    Component("System mass-margin reserve", 7.0398, 0.00, 0.00, 0.00, 0.30, 0.30, 0.30, "reserve"),
)

DRAWING_LABELS = {
    "Payload telescope": "PAY",
    "Electrical power system": "EPS",
    "ADCS assembly": "ADCS",
    "X-band communications": "COM",
    "Command and data handling": "CDH",
    "Propulsion hardware": "PROP",
    "Propellant": "FUEL",
}


def total_mass_kg(components=COMPONENTS):
    return sum(component.mass_kg for component in components)


def centre_of_mass_m(components=COMPONENTS):
    mass = total_mass_kg(components)
    return tuple(
        sum(c.mass_kg * getattr(c, axis) for c in components) / mass
        for axis in ("x_m", "y_m", "z_m")
    )


def deployed_envelope_m():
    return (
        BUS_DIMS_M[0] + 2.0 * SOLAR_WING_DIMS_M[0],
        max(BUS_DIMS_M[1], SOLAR_WING_DIMS_M[1]),
        BUS_DIMS_M[2],
    )


def component_inside_bus(component):
    if component.category == "distributed":
        return True
    for centre, size, bus in zip(
        (component.x_m, component.y_m, component.z_m),
        (component.size_x_m, component.size_y_m, component.size_z_m),
        BUS_DIMS_M,
    ):
        if abs(centre) + size / 2.0 > bus / 2.0 + 1e-12:
            return False
    return True


def box_vertices(centre, size):
    cx, cy, cz = centre; sx, sy, sz = (value / 2.0 for value in size)
    return np.array([(cx + dx, cy + dy, cz + dz) for dx in (-sx, sx) for dy in (-sy, sy) for dz in (-sz, sz)])


BOX_FACES = ((0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5))


def draw_box(ax, centre, size, colour, alpha=0.75):
    vertices = box_vertices(centre, size)
    faces = [[vertices[index] for index in face] for face in BOX_FACES]
    ax.add_collection3d(Poly3DCollection(faces, facecolors=colour, edgecolors="black", linewidths=0.4, alpha=alpha))


def plot_configuration(output):
    fig = plt.figure(figsize=(10, 7)); ax = fig.add_subplot(111, projection="3d")
    draw_box(ax, (0, 0, 0), BUS_DIMS_M, "lightgrey", 0.16)
    colours = {"payload": "#e76f51", "equipment": "#457b9d", "reserve": "#f4a261"}
    for component in COMPONENTS:
        if component.category not in {"distributed", "reserve", "contained"}:
            draw_box(ax, (component.x_m, component.y_m, component.z_m), (component.size_x_m, component.size_y_m, component.size_z_m), colours.get(component.category, "#457b9d"), 0.72)
    wing_z = 0.10
    for sign in (-1, 1):
        wing_x = sign * (BUS_DIMS_M[0] / 2.0 + SOLAR_WING_DIMS_M[0] / 2.0)
        draw_box(ax, (wing_x, 0, wing_z), SOLAR_WING_DIMS_M, "#264653", 0.85)
    com = centre_of_mass_m(); ax.scatter(*com, color="red", s=65, marker="x", label="Calculated centre of mass")
    envelope = deployed_envelope_m(); ax.set_xlim(-envelope[0] / 2 - 0.1, envelope[0] / 2 + 0.1); ax.set_ylim(-0.5, 0.5); ax.set_zlim(-0.5, 0.5)
    ax.set(xlabel="x [m]", ylabel="y [m]", zlabel="z [m]", title="Preliminary deployed spacecraft configuration")
    ax.set_box_aspect((envelope[0], 1.0, 1.0)); ax.legend(); fig.tight_layout(); fig.savefig(output / "spacecraft_configuration_3d.png", dpi=220); plt.close(fig)


def plot_orthographic(output):
    fig, axes = plt.subplots(1, 3, figsize=(13, 5))
    views = (("Front (x-z)", 0, 2), ("Side (y-z)", 1, 2), ("Top (x-y)", 0, 1))
    coordinates = ("x_m", "y_m", "z_m"); sizes = ("size_x_m", "size_y_m", "size_z_m")
    for ax, (title, horizontal, vertical) in zip(axes, views):
        bus_w, bus_h = BUS_DIMS_M[horizontal], BUS_DIMS_M[vertical]
        ax.add_patch(plt.Rectangle((-bus_w / 2, -bus_h / 2), bus_w, bus_h, fill=False, linewidth=2))
        for component in COMPONENTS:
            if component.category in {"distributed", "reserve", "contained"}: continue
            x = getattr(component, coordinates[horizontal]); y = getattr(component, coordinates[vertical])
            width = getattr(component, sizes[horizontal]); height = getattr(component, sizes[vertical])
            ax.add_patch(plt.Rectangle((x - width / 2, y - height / 2), width, height, alpha=0.35))
            ax.text(x, y, DRAWING_LABELS[component.name], ha="center", va="center", fontsize=8, fontweight="bold")
        ax.set(title=f"{title}\nBus {bus_w:.2f} x {bus_h:.2f} m", xlabel=f"{coordinates[horizontal][0]} [m]", ylabel=f"{coordinates[vertical][0]} [m]")
        ax.set_aspect("equal"); ax.grid(alpha=0.25); ax.set_xlim(-bus_w / 2 - 0.08, bus_w / 2 + 0.08); ax.set_ylim(-bus_h / 2 - 0.08, bus_h / 2 + 0.08)
    fig.suptitle("CAD-ready preliminary internal arrangement")
    fig.text(0.5, 0.02, "PAY payload · EPS electrical power · ADCS attitude control · COM communications · CDH command/data · PROP propulsion", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.06, 1, 0.95)); fig.savefig(output / "orthographic_dimension_drawing.png", dpi=220); plt.close(fig)


def triangle_normal(a, b, c):
    normal = np.cross(np.array(b) - np.array(a), np.array(c) - np.array(a)); magnitude = np.linalg.norm(normal)
    return normal / magnitude if magnitude else normal


def box_triangles(centre, size):
    vertices = box_vertices(centre, size); triangles = []
    for face in BOX_FACES:
        a, b, c, d = [vertices[i] for i in face]; triangles.extend(((a, b, c), (a, c, d)))
    return triangles


def cylinder_triangles(radius, length, centre_z, segments=32):
    triangles = []; z0, z1 = centre_z - length / 2, centre_z + length / 2
    for index in range(segments):
        a0, a1 = 2 * math.pi * index / segments, 2 * math.pi * (index + 1) / segments
        p0, p1 = (radius * math.cos(a0), radius * math.sin(a0), z0), (radius * math.cos(a1), radius * math.sin(a1), z0)
        q0, q1 = (p0[0], p0[1], z1), (p1[0], p1[1], z1)
        triangles.extend(((p0, p1, q1), (p0, q1, q0), ((0, 0, z0), p1, p0), ((0, 0, z1), q0, q1)))
    return triangles


def write_stl(path):
    triangles = box_triangles((0, 0, 0), BUS_DIMS_M)
    wing_z = 0.10
    for sign in (-1, 1):
        wing_x = sign * (BUS_DIMS_M[0] / 2 + SOLAR_WING_DIMS_M[0] / 2)
        triangles += box_triangles((wing_x, 0, wing_z), SOLAR_WING_DIMS_M)
    triangles += cylinder_triangles(0.10, 0.12, -BUS_DIMS_M[2] / 2 - 0.06)
    with path.open("w", encoding="ascii") as stream:
        stream.write("solid earth_observation_spacecraft\n")
        for a, b, c in triangles:
            n = triangle_normal(a, b, c); stream.write(f" facet normal {n[0]:.7e} {n[1]:.7e} {n[2]:.7e}\n  outer loop\n")
            for vertex in (a, b, c): stream.write(f"   vertex {vertex[0]:.7e} {vertex[1]:.7e} {vertex[2]:.7e}\n")
            stream.write("  endloop\n endfacet\n")
        stream.write("endsolid earth_observation_spacecraft\n")


def write_component_csv(path):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(asdict(COMPONENTS[0]).keys())); writer.writeheader(); writer.writerows(asdict(c) for c in COMPONENTS)


def write_dimension_sheet(path):
    subsystem = evaluate_subsystems(); com = centre_of_mass_m(); deployed = deployed_envelope_m()
    text = f"""# Preliminary CAD Dimension Sheet\n\nConcept geometry only; dimensions are not manufacturing tolerances.\n\n- Stowed bus envelope: {BUS_DIMS_M[0]:.2f} x {BUS_DIMS_M[1]:.2f} x {BUS_DIMS_M[2]:.2f} m\n- Deployed envelope: {deployed[0]:.2f} x {deployed[1]:.2f} x {deployed[2]:.2f} m\n- Payload bounding envelope: 0.24 x 0.24 x 0.65 m\n- Two solar wings: {SOLAR_WING_DIMS_M[0]:.2f} x {SOLAR_WING_DIMS_M[1]:.2f} m each\n- Selected solar area: {SELECTED_SOLAR_AREA_M2:.3f} m2; required {subsystem.required_solar_array_area_m2:.3f} m2\n- Selected radiator area: {SELECTED_RADIATOR_AREA_M2:.3f} m2; required {subsystem.radiator_area_m2:.3f} m2\n- Configured wet mass: {total_mass_kg():.3f} kg\n- Centre of mass from bus centre: ({com[0]:.4f}, {com[1]:.4f}, {com[2]:.4f}) m\n\nThe STL represents the external concept envelope with deployed arrays and a payload aperture. Rebuild as a parametric assembly in SolidWorks before structural analysis.\n"""
    path.write_text(text, encoding="utf-8")


def main():
    output = Path(__file__).resolve().parent / "results" / "spacecraft_configuration"; output.mkdir(parents=True, exist_ok=True)
    plot_configuration(output); plot_orthographic(output); write_component_csv(output / "component_layout.csv"); write_stl(output / "spacecraft_concept.stl"); write_dimension_sheet(output / "CAD_DIMENSION_SHEET.md")
    subsystem = evaluate_subsystems(); com = centre_of_mass_m()
    print("PHASE 8 PRELIMINARY SPACECRAFT CONFIGURATION")
    print(f"bus_dimensions_m: {BUS_DIMS_M}"); print(f"deployed_envelope_m: {deployed_envelope_m()}"); print(f"configured_mass_kg: {total_mass_kg():.3f}"); print(f"centre_of_mass_m: {com}")
    print(f"solar_area_selected_required_m2: {SELECTED_SOLAR_AREA_M2:.3f} / {subsystem.required_solar_array_area_m2:.3f}"); print(f"radiator_area_selected_required_m2: {SELECTED_RADIATOR_AREA_M2:.3f} / {subsystem.radiator_area_m2:.3f}")


if __name__ == "__main__": main()
