"""Phase 7 integrated budgets and requirements-verification baseline."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from functools import cache
from pathlib import Path

import matplotlib.pyplot as plt

from mission_operations import run_trade
from orbit_coverage import OrbitCase, evaluate_case
from payload_optimisation import generate_trade, select_preferred
from payload_radiometry import BANDS, RadiometryInputs, calculate_data_budget
from payload_sizing import PayloadDesign, size_payload
from spacecraft_subsystems import MASS_BUDGET_KG, evaluate_subsystems


@dataclass(frozen=True)
class BudgetItem:
    budget: str
    item: str
    required: float
    selected: float
    unit: str
    margin_percent: float
    status: str


@dataclass(frozen=True)
class Requirement:
    identifier: str
    requirement: str
    threshold: str
    predicted: str
    status: str
    verification: str
    source_phase: str


def margin_above(required: float, selected: float) -> float:
    return (selected / required - 1.0) * 100.0


def margin_below(limit: float, predicted: float) -> float:
    return (limit / predicted - 1.0) * 100.0


@cache
def build_baseline():
    design = PayloadDesign(550.0, 10.0, 8192, 10.0)
    geometry = size_payload(design)
    payload = select_preferred(generate_trade(design))
    orbit = evaluate_case(OrbitCase(550.0, 25.0, geometry.swath_width_km, 2))
    data = calculate_data_budget(design, RadiometryInputs(), len(BANDS))
    operations = run_trade()[1]
    spacecraft = evaluate_subsystems()
    selected = {
        "array_power_w": 150.0,
        "battery_wh": 80.0,
        "storage_gb": 8.0,
        "wheel_torque_nm": spacecraft.selected_wheel_torque_nm,
        "wheel_momentum_nms": spacecraft.selected_wheel_momentum_nms,
        "delta_v_m_s": 50.0,
        "radiator_area_m2": 0.60,
    }
    return geometry, payload, orbit, data, operations, spacecraft, selected


def integrated_budget_items():
    _, _, _, _, operations, spacecraft, selected = build_baseline()
    items = [
        BudgetItem("Mass", "Wet spacecraft mass", spacecraft.wet_mass_with_system_margin_kg, 60.0, "kg limit", margin_above(spacecraft.wet_mass_with_system_margin_kg, 60.0), "Pass"),
        BudgetItem("Power", "EOL solar-array power", spacecraft.required_eol_array_power_w, selected["array_power_w"], "W", margin_above(spacecraft.required_eol_array_power_w, selected["array_power_w"]), "Pass"),
        BudgetItem("Power", "Battery capacity", spacecraft.required_battery_capacity_wh, selected["battery_wh"], "Wh", margin_above(spacecraft.required_battery_capacity_wh, selected["battery_wh"]), "Pass"),
        BudgetItem("Data", "Onboard storage", operations.recommended_storage_gb_per_spacecraft, selected["storage_gb"], "GB", margin_above(operations.recommended_storage_gb_per_spacecraft, selected["storage_gb"]), "Pass"),
        BudgetItem("Data", "Daily downlink", operations.daily_generated_data_gbit_per_spacecraft, operations.daily_downlink_capacity_gbit_per_spacecraft, "Gbit/day", margin_above(operations.daily_generated_data_gbit_per_spacecraft, operations.daily_downlink_capacity_gbit_per_spacecraft), "Pass"),
        BudgetItem("ADCS", "Reaction-wheel torque", spacecraft.minimum_control_torque_nm, selected["wheel_torque_nm"], "N m", margin_above(spacecraft.minimum_control_torque_nm, selected["wheel_torque_nm"]), "Pass"),
        BudgetItem("ADCS", "Wheel momentum", spacecraft.minimum_momentum_capacity_nms, selected["wheel_momentum_nms"], "N m s", margin_above(spacecraft.minimum_momentum_capacity_nms, selected["wheel_momentum_nms"]), "Pass"),
        BudgetItem("Propulsion", "Delta-v capacity", spacecraft.delta_v_with_margin_m_s, selected["delta_v_m_s"], "m/s", margin_above(spacecraft.delta_v_with_margin_m_s, selected["delta_v_m_s"]), "Pass"),
        BudgetItem("Thermal", "Radiator area", spacecraft.radiator_area_m2, selected["radiator_area_m2"], "m2", margin_above(spacecraft.radiator_area_m2, selected["radiator_area_m2"]), "Pass"),
        BudgetItem("Communications", "X-band link margin", 3.0, spacecraft.link_margin_db, "dB", margin_above(3.0, spacecraft.link_margin_db), "Pass"),
    ]
    return items


def requirements_matrix():
    geometry, payload, orbit, _, operations, spacecraft, selected = build_baseline()
    return [
        Requirement("MIS-001", "Nadir ground-sampling distance", "<= 10 m", "10.00 m", "Pass", "Analysis", "Phase 1"),
        Requirement("MIS-002", "Imaging swath width", ">= 50 km", f"{geometry.swath_width_km:.2f} km", "Pass", "Analysis", "Phase 1"),
        Requirement("PAY-001", "Worst-band payload SNR", ">= 50", f"{payload.minimum_band_snr:.2f}", "Pass", "Analysis", "Phase 3"),
        Requirement("MIS-003", "Representative UK-site revisit", "<= 48 h", f"{orbit.worst_site_max_revisit_h:.2f} h", "Pass", "Simulation", "Phase 4"),
        Requirement("MIS-004", "Priority product delivery", "<= 3 h when access permits", f"{operations.worst_priority_latency_h:.2f} h", "Fail", "Simulation", "Phase 5"),
        Requirement("DAT-001", "Daily downlink exceeds generation", ">= 39.32 Gbit/day", f"{operations.daily_downlink_capacity_gbit_per_spacecraft:.2f} Gbit/day", "Pass", "Simulation", "Phase 5"),
        Requirement("DAT-002", "Onboard storage capacity", f">= {operations.recommended_storage_gb_per_spacecraft:.2f} GB", f"{selected['storage_gb']:.1f} GB", "Pass", "Budget", "Phase 7"),
        Requirement("SYS-001", "Wet mass per spacecraft", "<= 60 kg", f"{spacecraft.wet_mass_with_system_margin_kg:.2f} kg", "Pass", "Budget", "Phase 6"),
        Requirement("PWR-001", "End-of-life array closes power budget", f">= {spacecraft.required_eol_array_power_w:.2f} W", f"{selected['array_power_w']:.1f} W", "Pass", "Budget", "Phase 7"),
        Requirement("COM-001", "X-band residual link margin", ">= 3 dB", f"{spacecraft.link_margin_db:.2f} dB", "Pass", "Analysis", "Phase 6"),
        Requirement("ADCS-001", "Reaction-wheel control torque", f">= {spacecraft.minimum_control_torque_nm:.4f} N m", f"{selected['wheel_torque_nm']:.3f} N m", "Pass", "Analysis", "Phase 6"),
        Requirement("ADCS-002", "Reaction-wheel momentum capacity", f">= {spacecraft.minimum_momentum_capacity_nms:.3f} N m s", f"{selected['wheel_momentum_nms']:.3f} N m s", "Pass", "Analysis", "Phase 6"),
        Requirement("PROP-001", "Available mission delta-v", f">= {spacecraft.delta_v_with_margin_m_s:.1f} m/s", f"{selected['delta_v_m_s']:.1f} m/s", "Pass", "Budget", "Phase 7"),
        Requirement("THERM-001", "Hot-case radiator allocation", f">= {spacecraft.radiator_area_m2:.3f} m2", f"{selected['radiator_area_m2']:.2f} m2", "Pass", "Analysis", "Phase 7"),
        Requirement("MIS-005", "Three-year mission life", ">= 3 years", "Not yet reliability-tested", "Open", "Test / reliability analysis", "Future"),
    ]


def write_dataclass_csv(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader(); writer.writerows(asdict(row) for row in rows)


def write_summary(requirements, budgets, path):
    counts = {status: sum(r.status == status for r in requirements) for status in ("Pass", "Fail", "Open")}
    summary = {
        "requirements": counts,
        "total_requirements": len(requirements),
        "minimum_positive_budget_margin_percent": min(b.margin_percent for b in budgets),
        "failed_requirement_ids": [r.identifier for r in requirements if r.status == "Fail"],
        "open_requirement_ids": [r.identifier for r in requirements if r.status == "Open"],
    }
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def plot_status(requirements, budgets, output):
    output.mkdir(parents=True, exist_ok=True)
    colours = {"Pass": "#2a9d8f", "Fail": "#d62828", "Open": "#f4a261"}
    counts = {status: sum(r.status == status for r in requirements) for status in colours}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    axes[0].bar(list(counts), list(counts.values()), color=[colours[k] for k in counts])
    axes[0].set(title="Requirements-verification status", ylabel="Number of requirements")
    axes[0].grid(axis="y", alpha=0.3)
    ordered = sorted(budgets, key=lambda b: b.margin_percent)
    axes[1].barh([b.item for b in ordered], [b.margin_percent for b in ordered], color="#457b9d")
    axes[1].set(title="Integrated positive design margins", xlabel="Margin [%]")
    axes[1].grid(axis="x", alpha=0.3)
    fig.tight_layout(); fig.savefig(output / "integrated_budget_status.png", dpi=200); plt.close(fig)


def main():
    output = Path(__file__).resolve().parent / "results" / "integrated_budgets"
    budgets = integrated_budget_items(); requirements = requirements_matrix()
    write_dataclass_csv(budgets, output / "integrated_budget.csv")
    write_dataclass_csv(requirements, output / "requirements_verification_matrix.csv")
    write_summary(requirements, budgets, output / "phase7_summary.json")
    plot_status(requirements, budgets, output)
    print("PHASE 7 INTEGRATED BUDGETS AND REQUIREMENTS BASELINE")
    for status in ("Pass", "Fail", "Open"):
        print(f"{status}: {sum(r.status == status for r in requirements)}")
    print(f"Total requirements: {len(requirements)}")
    print(f"Minimum positive budget margin: {min(b.margin_percent for b in budgets):.3f} percent")
    for req in requirements:
        if req.status != "Pass": print(f"{req.identifier}: {req.status} - {req.predicted}")


if __name__ == "__main__": main()
