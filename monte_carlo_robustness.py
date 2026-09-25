"""Phase 9 Monte Carlo robustness and sensitivity analysis.

The simulation uses transparent response-surface relationships anchored to the
deterministic Phase 3-7 baseline. It is a concept-design uncertainty study, not
a substitute for hardware qualification or high-fidelity subsystem models.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


SEED = 260925
DEFAULT_CASES = 5000


@dataclass(frozen=True)
class MonteCarloSummary:
    cases: int
    baseline_budget_success_percent: float
    hardened_budget_success_percent: float
    full_mission_success_percent: float
    dominant_baseline_failure: str
    dominant_sensitivity_driver: str


def generate_uncertainties(cases=DEFAULT_CASES, seed=SEED):
    rng = np.random.default_rng(seed)
    return {
        "payload_signal_factor": rng.lognormal(0.0, 0.12, cases),
        "mass_growth_factor": rng.normal(1.0, 0.035, cases),
        "power_load_factor": rng.normal(1.0, 0.08, cases),
        "annual_solar_degradation": np.clip(rng.normal(0.025, 0.006, cases), 0.005, 0.06),
        "extra_communications_loss_db": rng.normal(0.0, 1.30, cases),
        "inertia_factor": rng.normal(1.0, 0.08, cases),
        "slew_time_factor": np.clip(rng.normal(1.0, 0.05, cases), 0.80, 1.20),
        "disturbance_factor": rng.lognormal(0.0, 0.30, cases),
        "delta_v_factor": np.clip(rng.normal(1.0, 0.12, cases), 0.65, 1.45),
        "thermal_load_factor": rng.normal(1.0, 0.08, cases),
        "radiator_performance_factor": rng.normal(1.0, 0.06, cases),
        "ground_availability": np.clip(rng.beta(36.0, 4.0, cases), 0.60, 0.995),
        "schedule_factor": rng.uniform(0.80, 1.20, cases),
        "data_volume_factor": np.clip(rng.normal(1.0, 0.12, cases), 0.60, 1.50),
    }


def run_monte_carlo(cases=DEFAULT_CASES, seed=SEED):
    u = generate_uncertainties(cases, seed)
    results = {}
    results["snr"] = 50.6025 * np.sqrt(u["payload_signal_factor"])
    results["wet_mass_kg"] = 55.2920 * u["mass_growth_factor"]
    nominal_eol = (1.0 - 0.025) ** 3
    sampled_eol = (1.0 - u["annual_solar_degradation"]) ** 3
    results["required_array_power_w"] = 130.3459 * u["power_load_factor"] * nominal_eol / sampled_eol
    results["link_margin_db"] = 3.8553 - u["extra_communications_loss_db"]
    results["required_wheel_torque_nm"] = 0.0096963 * u["inertia_factor"] / u["slew_time_factor"]**2
    results["required_wheel_momentum_nms"] = 0.0860849 * u["disturbance_factor"]
    results["required_delta_v_m_s"] = 48.0 * u["delta_v_factor"]
    results["required_radiator_area_m2"] = 0.5343066 * u["thermal_load_factor"] / u["radiator_performance_factor"]
    results["generated_data_gbit_day"] = 39.3216 * u["data_volume_factor"]
    results["downlink_capacity_gbit_day"] = 562.275 * u["ground_availability"] / 0.90
    results["required_storage_gb"] = 2.94912 * u["data_volume_factor"] * 0.90 / u["ground_availability"]
    results["priority_latency_h"] = 6.99834 * 0.90 / u["ground_availability"] * u["schedule_factor"]

    baseline_passes = {
        "Payload SNR": results["snr"] >= 50.0,
        "Wet mass": results["wet_mass_kg"] <= 60.0,
        "Solar-array power": results["required_array_power_w"] <= 150.0,
        "X-band margin": results["link_margin_db"] >= 3.0,
        "Wheel torque": results["required_wheel_torque_nm"] <= 0.010,
        "Wheel momentum": results["required_wheel_momentum_nms"] <= 0.100,
        "Delta-v": results["required_delta_v_m_s"] <= 50.0,
        "Radiator area": results["required_radiator_area_m2"] <= 0.600,
        "Daily data balance": results["downlink_capacity_gbit_day"] >= results["generated_data_gbit_day"],
        "Onboard storage": results["required_storage_gb"] <= 8.0,
    }
    hardened_passes = {
        "Payload SNR": results["snr"] * (180.0 / 160.0) >= 50.0,
        "Wet mass": results["wet_mass_kg"] <= 60.0,
        "Solar-array power": results["required_array_power_w"] <= 180.0,
        "X-band margin": results["link_margin_db"] + 3.0 >= 3.0,
        "Wheel torque": results["required_wheel_torque_nm"] <= 0.015,
        "Wheel momentum": results["required_wheel_momentum_nms"] <= 0.150,
        "Delta-v": results["required_delta_v_m_s"] <= 60.0,
        "Radiator area": results["required_radiator_area_m2"] <= 0.700,
        "Daily data balance": results["downlink_capacity_gbit_day"] >= results["generated_data_gbit_day"],
        "Onboard storage": results["required_storage_gb"] <= 16.0,
    }
    baseline_system = np.logical_and.reduce(list(baseline_passes.values()))
    hardened_system = np.logical_and.reduce(list(hardened_passes.values()))
    delivery_pass = results["priority_latency_h"] <= 3.0
    full_mission = baseline_system & delivery_pass

    margins = np.vstack([
        (results["snr"] - 50.0) / 50.0,
        (60.0 - results["wet_mass_kg"]) / 60.0,
        (150.0 - results["required_array_power_w"]) / 150.0,
        (results["link_margin_db"] - 3.0) / 3.0,
        (0.010 - results["required_wheel_torque_nm"]) / 0.010,
        (0.100 - results["required_wheel_momentum_nms"]) / 0.100,
        (50.0 - results["required_delta_v_m_s"]) / 50.0,
        (0.600 - results["required_radiator_area_m2"]) / 0.600,
    ])
    minimum_margin = np.min(margins, axis=0)
    sensitivity_inputs = {
        "Payload signal": u["payload_signal_factor"],
        "Mass growth": u["mass_growth_factor"],
        "Power load": u["power_load_factor"],
        "Communications loss": u["extra_communications_loss_db"],
        "Spacecraft inertia": u["inertia_factor"],
        "Disturbance torque": u["disturbance_factor"],
        "Delta-v demand": u["delta_v_factor"],
        "Thermal load": u["thermal_load_factor"],
    }
    sensitivities = {name: float(np.corrcoef(values, minimum_margin)[0, 1]) for name, values in sensitivity_inputs.items()}
    pass_rates = {name: float(np.mean(values) * 100.0) for name, values in baseline_passes.items()}
    failure = min(pass_rates, key=pass_rates.get)
    driver = max(sensitivities, key=lambda name: abs(sensitivities[name]))
    summary = MonteCarloSummary(
        cases=cases,
        baseline_budget_success_percent=float(np.mean(baseline_system) * 100.0),
        hardened_budget_success_percent=float(np.mean(hardened_system) * 100.0),
        full_mission_success_percent=float(np.mean(full_mission) * 100.0),
        dominant_baseline_failure=failure,
        dominant_sensitivity_driver=driver,
    )
    return u, results, baseline_passes, pass_rates, sensitivities, summary


def write_case_csv(u, results, baseline_passes, path):
    fields = ["case"] + list(u) + list(results) + [f"pass_{name.lower().replace(' ', '_').replace('-', '_')}" for name in baseline_passes]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream); writer.writerow(fields)
        for index in range(len(next(iter(u.values())))):
            writer.writerow([index + 1] + [u[name][index] for name in u] + [results[name][index] for name in results] + [int(baseline_passes[name][index]) for name in baseline_passes])


def write_risk_csv(pass_rates, sensitivities, path):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream); writer.writerow(["metric", "value_percent_or_correlation", "type"])
        for name, value in pass_rates.items(): writer.writerow([name, value, "requirement_pass_rate_percent"])
        for name, value in sensitivities.items(): writer.writerow([name, value, "minimum_margin_correlation"])


def plot_results(pass_rates, sensitivities, summary, path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    ordered_pass = sorted(pass_rates.items(), key=lambda item: item[1])
    colours = ["#d62828" if value < 90 else "#f4a261" if value < 99 else "#2a9d8f" for _, value in ordered_pass]
    axes[0].barh([name for name, _ in ordered_pass], [value for _, value in ordered_pass], color=colours)
    axes[0].axvline(95.0, color="black", linestyle="--", label="95% robustness target")
    axes[0].set(xlim=(0, 105), xlabel="Monte Carlo pass rate [%]", title="Baseline constraint robustness"); axes[0].legend(); axes[0].grid(axis="x", alpha=0.3)
    ordered_sensitivity = sorted(sensitivities.items(), key=lambda item: abs(item[1]))
    axes[1].barh([name for name, _ in ordered_sensitivity], [value for _, value in ordered_sensitivity], color="#457b9d")
    axes[1].axvline(0.0, color="black", linewidth=0.8); axes[1].set(xlabel="Correlation with minimum design margin", title="Global sensitivity ranking"); axes[1].grid(axis="x", alpha=0.3)
    fig.suptitle(f"{summary.cases:,} cases · baseline closure {summary.baseline_budget_success_percent:.1f}% · hardened closure {summary.hardened_budget_success_percent:.1f}%")
    fig.tight_layout(); fig.savefig(path, dpi=220); plt.close(fig)


def plot_distributions(results, path):
    plots = (("snr", 50.0, "Worst-band SNR"), ("link_margin_db", 3.0, "X-band margin [dB]"), ("required_wheel_torque_nm", 0.010, "Required wheel torque [N m]"), ("required_delta_v_m_s", 50.0, "Required delta-v [m/s]"))
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for ax, (key, limit, label) in zip(axes.flat, plots):
        ax.hist(results[key], bins=45, color="#457b9d", alpha=0.85); ax.axvline(limit, color="#d62828", linestyle="--", label="Baseline threshold")
        ax.set(xlabel=label, ylabel="Cases"); ax.legend(); ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Selected Monte Carlo output distributions"); fig.tight_layout(); fig.savefig(path, dpi=220); plt.close(fig)


def main():
    output = Path(__file__).resolve().parent / "results" / "monte_carlo_robustness"; output.mkdir(parents=True, exist_ok=True)
    u, results, passes, rates, sensitivities, summary = run_monte_carlo()
    write_case_csv(u, results, passes, output / "monte_carlo_cases.csv"); write_risk_csv(rates, sensitivities, output / "risk_summary.csv")
    (output / "monte_carlo_summary.json").write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
    plot_results(rates, sensitivities, summary, output / "robustness_and_sensitivity.png"); plot_distributions(results, output / "selected_distributions.png")
    print("PHASE 9 MONTE CARLO ROBUSTNESS AND SENSITIVITY")
    for key, value in asdict(summary).items(): print(f"{key}: {value}")
    for name, value in sorted(rates.items(), key=lambda item: item[1]): print(f"{name}_pass_percent: {value:.2f}")


if __name__ == "__main__": main()
