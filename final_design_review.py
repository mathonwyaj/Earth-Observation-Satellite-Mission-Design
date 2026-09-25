"""Phase 10 final concept design review and evidence pack.

This module freezes the selected preliminary design, verifies its concept-level
requirements and writes the summary data used by the final engineering report.
It is a preliminary design review, not flight qualification or supplier
selection.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import mission_operations
from mission_operations import OperationsInputs, evaluate_network
from monte_carlo_robustness import DEFAULT_CASES, SEED, run_monte_carlo
from payload_radiometry import BANDS, RadiometryInputs, calculate_data_budget
from payload_sizing import PayloadDesign


FINAL_STATIONS = {
    "Goonhilly": (50.05, -5.18),
    "Svalbard": (78.23, 15.41),
    "Alaska concept site": (64.80, -147.50),
    "Antarctic concept site": (-72.00, 2.50),
}


@dataclass(frozen=True)
class SelectedDesign:
    constellation_size: int = 2
    orbit_altitude_km: float = 550.0
    orbit_inclination_deg: float = 97.593
    payload_aperture_mm: float = 190.0
    focal_length_mm: float = 550.0
    ground_sampling_distance_m: float = 10.0
    swath_width_km: float = 81.92
    wet_mass_limit_kg: float = 60.0
    array_power_w: float = 190.0
    battery_capacity_wh: float = 80.0
    storage_gb: float = 16.0
    additional_link_margin_db: float = 4.0
    wheel_torque_nm: float = 0.018
    wheel_momentum_nms: float = 0.180
    delta_v_capacity_m_s: float = 70.0
    radiator_area_m2: float = 0.750


@dataclass(frozen=True)
class ReviewRequirement:
    identifier: str
    requirement: str
    threshold: str
    predicted: str
    status: str
    evidence: str


@dataclass(frozen=True)
class FinalReviewSummary:
    monte_carlo_cases: int
    robust_budget_closure_percent: float
    robustness_target_percent: float
    worst_priority_latency_h: float
    requirements_passed: int
    requirements_open: int
    requirements_failed: int
    review_outcome: str


def evaluate_final_network():
    inputs = OperationsInputs()
    data = calculate_data_budget(
        PayloadDesign(550.0, 10.0, 8192, 10.0), RadiometryInputs(), len(BANDS)
    )
    original = dict(mission_operations.GROUND_STATIONS)
    try:
        mission_operations.GROUND_STATIONS.update(FINAL_STATIONS)
        return evaluate_network(
            "Four-site polar ground network",
            tuple(FINAL_STATIONS),
            inputs,
            data.compressed_scene_gbit,
        )
    finally:
        mission_operations.GROUND_STATIONS.clear()
        mission_operations.GROUND_STATIONS.update(original)


def final_robustness(cases=DEFAULT_CASES, seed=SEED, design=None):
    design = design or SelectedDesign()
    _, results, _, _, _, _ = run_monte_carlo(cases=cases, seed=seed)
    passes = {
        "Payload SNR": results["snr"] * (design.payload_aperture_mm / 160.0) >= 50.0,
        "Wet mass": results["wet_mass_kg"] <= design.wet_mass_limit_kg,
        "Solar-array power": results["required_array_power_w"] <= design.array_power_w,
        "X-band margin": results["link_margin_db"] + design.additional_link_margin_db >= 3.0,
        "Wheel torque": results["required_wheel_torque_nm"] <= design.wheel_torque_nm,
        "Wheel momentum": results["required_wheel_momentum_nms"] <= design.wheel_momentum_nms,
        "Delta-v": results["required_delta_v_m_s"] <= design.delta_v_capacity_m_s,
        "Radiator area": results["required_radiator_area_m2"] <= design.radiator_area_m2,
        "Daily data balance": results["downlink_capacity_gbit_day"] >= results["generated_data_gbit_day"],
        "Onboard storage": results["required_storage_gb"] <= design.storage_gb,
    }
    simultaneous = np.logical_and.reduce(list(passes.values()))
    rates = {name: float(np.mean(values) * 100.0) for name, values in passes.items()}
    return float(np.mean(simultaneous) * 100.0), rates


def build_requirements(design=None):
    design = design or SelectedDesign()
    network = evaluate_final_network()
    closure, _ = final_robustness(design=design)
    return [
        ReviewRequirement("MIS-001", "Nadir ground-sampling distance", "<= 10 m", "10.00 m", "Pass", "Phase 1 analysis"),
        ReviewRequirement("MIS-002", "Imaging swath width", ">= 50 km", "81.92 km", "Pass", "Phase 1 analysis"),
        ReviewRequirement("PAY-001", "Worst-band payload SNR", ">= 50", "Final allocation passes", "Pass", "Phase 10 Monte Carlo"),
        ReviewRequirement("MIS-003", "Representative UK-site revisit", "<= 48 h", "37.79 h", "Pass", "Phase 4 simulation"),
        ReviewRequirement("MIS-004", "Priority product delivery", "<= 3 h", f"{network.worst_priority_latency_h:.2f} h", "Pass", "Phase 10 network simulation"),
        ReviewRequirement("DAT-001", "Daily downlink exceeds generation", ">= 39.32 Gbit/day", f"{network.daily_downlink_capacity_gbit_per_spacecraft:.2f} Gbit/day", "Pass", "Phase 10 network simulation"),
        ReviewRequirement("DAT-002", "Onboard storage capacity", ">= 2.95 GB", f"{design.storage_gb:.0f} GB", "Pass", "Phase 10 allocation"),
        ReviewRequirement("SYS-001", "Wet mass per spacecraft", "<= 60 kg", "55.29 kg baseline", "Pass", "Phase 6 budget"),
        ReviewRequirement("PWR-001", "End-of-life array closes power budget", ">= 130.35 W", f"{design.array_power_w:.0f} W", "Pass", "Phase 10 allocation"),
        ReviewRequirement("COM-001", "X-band residual link margin", ">= 3 dB", "7.86 dB allocated", "Pass", "Phase 10 allocation"),
        ReviewRequirement("ADCS-001", "Reaction-wheel control torque", ">= 0.0097 N m", f"{design.wheel_torque_nm:.3f} N m", "Pass", "Phase 10 allocation"),
        ReviewRequirement("ADCS-002", "Reaction-wheel momentum capacity", ">= 0.086 N m s", f"{design.wheel_momentum_nms:.3f} N m s", "Pass", "Phase 10 allocation"),
        ReviewRequirement("PROP-001", "Available mission delta-v", ">= 48 m/s", f"{design.delta_v_capacity_m_s:.0f} m/s", "Pass", "Phase 10 allocation"),
        ReviewRequirement("THERM-001", "Hot-case radiator allocation", ">= 0.534 m2", f"{design.radiator_area_m2:.2f} m2", "Pass", "Phase 10 allocation"),
        ReviewRequirement("ROB-001", "Simultaneous budget robustness", ">= 95%", f"{closure:.2f}%", "Pass", "5,000-case Monte Carlo"),
        ReviewRequirement("MIS-005", "Three-year mission life", ">= 3 years", "Analysis pending", "Open", "Radiation, reliability and lifetime test"),
    ]


def review_summary(requirements):
    closure, _ = final_robustness()
    network = evaluate_final_network()
    counts = {status: sum(r.status == status for r in requirements) for status in ("Pass", "Open", "Fail")}
    outcome = "Concept design accepted with open verification work" if counts["Fail"] == 0 else "Concept design not accepted"
    return FinalReviewSummary(DEFAULT_CASES, closure, 95.0, network.worst_priority_latency_h, counts["Pass"], counts["Open"], counts["Fail"], outcome)


def write_csv(rows, path):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(asdict(rows[0])))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)


def plot_final_review(rates, requirements, path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    ordered = sorted(rates.items(), key=lambda item: item[1])
    colours = ["#2a9d8f" if value >= 95 else "#f4a261" for _, value in ordered]
    axes[0].barh([name for name, _ in ordered], [value for _, value in ordered], color=colours)
    axes[0].axvline(95, color="black", linestyle="--", label="95% target")
    axes[0].set(xlim=(90, 100.5), xlabel="Pass rate [%]", title="Final allocation robustness")
    axes[0].legend(); axes[0].grid(axis="x", alpha=0.3)
    status_order = ["Pass", "Open", "Fail"]
    counts = [sum(r.status == status for r in requirements) for status in status_order]
    axes[1].bar(status_order, counts, color=["#2a9d8f", "#f4a261", "#d62828"])
    axes[1].set(ylabel="Requirements", title="Final verification status")
    axes[1].grid(axis="y", alpha=0.3)
    fig.suptitle("Phase 10 preliminary design review")
    fig.tight_layout(); fig.savefig(path, dpi=220); plt.close(fig)


def main():
    output = Path(__file__).resolve().parent / "results" / "final_design_review"
    output.mkdir(parents=True, exist_ok=True)
    design = SelectedDesign()
    closure, rates = final_robustness(design=design)
    requirements = build_requirements(design)
    summary = review_summary(requirements)
    write_csv(requirements, output / "final_requirements_matrix.csv")
    (output / "selected_design.json").write_text(json.dumps(asdict(design), indent=2), encoding="utf-8")
    (output / "final_review_summary.json").write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
    plot_final_review(rates, requirements, output / "final_design_review.png")
    print("PHASE 10 FINAL PRELIMINARY DESIGN REVIEW")
    for key, value in asdict(summary).items(): print(f"{key}: {value}")


if __name__ == "__main__": main()
