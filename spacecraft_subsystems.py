"""Phase 6 preliminary spacecraft subsystem sizing.

The calculations are transparent concept-design estimates. Component choices,
environmental cases and margins require later vendor and mission validation.
"""

from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt

from orbit_coverage import orbital_period_min

G0 = 9.80665
SIGMA = 5.670374419e-8


@dataclass(frozen=True)
class SubsystemInputs:
    altitude_km: float = 550.0
    wet_mass_limit_kg: float = 60.0
    mission_life_years: float = 3.0
    eclipse_duration_min: float = 35.0
    sunlight_duration_min: float = 60.65
    sunlight_load_w: float = 65.0
    eclipse_load_w: float = 55.0
    imaging_power_w: float = 185.0
    imaging_time_s_day: float = 527.4
    downlink_power_w: float = 145.0
    downlink_time_s_day: float = 416.1
    power_margin: float = 0.30
    cell_bol_power_density_w_m2: float = 300.0
    solar_incidence_factor: float = 0.85
    power_path_efficiency: float = 0.85
    annual_degradation: float = 0.025
    battery_depth_of_discharge: float = 0.80
    battery_efficiency: float = 0.90
    battery_margin: float = 0.20
    xband_frequency_ghz: float = 8.2
    downlink_rate_mbps: float = 150.0
    transmitter_power_w: float = 15.0
    spacecraft_antenna_gain_dbi: float = 6.0
    transmit_losses_db: float = 1.0
    ground_gt_db_k: float = 25.0
    required_ebn0_db: float = 6.0
    implementation_loss_db: float = 2.0
    maximum_slant_range_km: float = 2_000.0
    maximum_slew_deg: float = 50.0
    slew_time_s: float = 60.0
    maximum_axis_inertia_kg_m2: float = 5.0
    control_torque_margin: float = 2.0
    disturbance_torque_nm: float = 5e-6
    momentum_accumulation_orbits: float = 3.0
    delta_v_base_m_s: float = 40.0
    delta_v_margin: float = 0.20
    propulsion_isp_s: float = 220.0
    hot_case_dissipation_w: float = 90.0
    radiator_temperature_k: float = 300.0
    effective_sink_temperature_k: float = 250.0
    radiator_emissivity: float = 0.85
    thermal_area_margin: float = 0.20


@dataclass(frozen=True)
class SubsystemResult:
    orbit_period_min: float
    average_operational_power_w: float
    required_eol_array_power_w: float
    required_solar_array_area_m2: float
    required_battery_capacity_wh: float
    link_ebn0_db: float
    link_margin_db: float
    minimum_control_torque_nm: float
    selected_wheel_torque_nm: float
    minimum_momentum_capacity_nms: float
    selected_wheel_momentum_nms: float
    delta_v_with_margin_m_s: float
    propellant_mass_kg: float
    radiator_area_m2: float
    dry_mass_before_system_margin_kg: float
    wet_mass_with_system_margin_kg: float
    wet_mass_margin_kg: float


MASS_BUDGET_KG = {
    "Payload": 7.932,
    "Structure and mechanisms": 10.0,
    "Electrical power": 7.0,
    "ADCS": 6.0,
    "Communications": 4.0,
    "Command and data handling": 2.0,
    "Thermal control": 4.0,
    "Propulsion hardware": 3.5,
    "Harness and integration": 2.5,
}


def power_sizing(inputs: SubsystemInputs) -> tuple[float, float, float, float]:
    day_s = 86400.0
    sun_fraction = inputs.sunlight_duration_min / (inputs.sunlight_duration_min + inputs.eclipse_duration_min)
    eclipse_fraction = 1.0 - sun_fraction
    imaging_increment_wh = max(0.0, inputs.imaging_power_w - inputs.sunlight_load_w) * inputs.imaging_time_s_day / 3600.0
    downlink_increment_wh = max(0.0, inputs.downlink_power_w - inputs.sunlight_load_w) * inputs.downlink_time_s_day / 3600.0
    daily_energy_wh = (inputs.sunlight_load_w * sun_fraction + inputs.eclipse_load_w * eclipse_fraction) * 24.0 + imaging_increment_wh + downlink_increment_wh
    average_power = daily_energy_wh / 24.0
    eclipse_energy_wh = inputs.eclipse_load_w * inputs.eclipse_duration_min / 60.0
    recharge_power = eclipse_energy_wh / (inputs.sunlight_duration_min / 60.0) / inputs.battery_efficiency
    required_eol_power = (inputs.sunlight_load_w + recharge_power) * (1.0 + inputs.power_margin)
    eol_factor = (1.0 - inputs.annual_degradation) ** inputs.mission_life_years
    usable_density = inputs.cell_bol_power_density_w_m2 * inputs.solar_incidence_factor * inputs.power_path_efficiency * eol_factor
    area = required_eol_power / usable_density
    battery_wh = eclipse_energy_wh / (inputs.battery_depth_of_discharge * inputs.battery_efficiency) * (1.0 + inputs.battery_margin)
    return average_power, required_eol_power, area, battery_wh


def xband_link_budget(inputs: SubsystemInputs) -> tuple[float, float]:
    frequency_hz = inputs.xband_frequency_ghz * 1e9
    wavelength_m = 299_792_458.0 / frequency_hz
    range_m = inputs.maximum_slant_range_km * 1_000.0
    free_space_loss_db = 20.0 * math.log10(4.0 * math.pi * range_m / wavelength_m)
    transmitter_dbw = 10.0 * math.log10(inputs.transmitter_power_w)
    eirp_dbw = transmitter_dbw + inputs.spacecraft_antenna_gain_dbi - inputs.transmit_losses_db
    cn0_db_hz = eirp_dbw - free_space_loss_db + inputs.ground_gt_db_k + 228.6
    ebn0_db = cn0_db_hz - 10.0 * math.log10(inputs.downlink_rate_mbps * 1e6)
    margin_db = ebn0_db - inputs.required_ebn0_db - inputs.implementation_loss_db
    return ebn0_db, margin_db


def adcs_sizing(inputs: SubsystemInputs) -> tuple[float, float, float, float]:
    angle_rad = math.radians(inputs.maximum_slew_deg)
    acceleration = 4.0 * angle_rad / inputs.slew_time_s**2
    minimum_torque = inputs.maximum_axis_inertia_kg_m2 * acceleration * inputs.control_torque_margin
    selected_torque = max(0.01, math.ceil(minimum_torque * 1000.0) / 1000.0)
    orbit_s = orbital_period_min(inputs.altitude_km) * 60.0
    minimum_momentum = inputs.disturbance_torque_nm * orbit_s * inputs.momentum_accumulation_orbits
    selected_momentum = max(0.10, math.ceil(minimum_momentum * 100.0) / 100.0)
    return minimum_torque, selected_torque, minimum_momentum, selected_momentum


def propulsion_sizing(inputs: SubsystemInputs) -> tuple[float, float]:
    delta_v = inputs.delta_v_base_m_s * (1.0 + inputs.delta_v_margin)
    propellant = inputs.wet_mass_limit_kg * (1.0 - math.exp(-delta_v / (G0 * inputs.propulsion_isp_s)))
    return delta_v, propellant


def thermal_sizing(inputs: SubsystemInputs) -> float:
    heat_flux = inputs.radiator_emissivity * SIGMA * (inputs.radiator_temperature_k**4 - inputs.effective_sink_temperature_k**4)
    return inputs.hot_case_dissipation_w / heat_flux * (1.0 + inputs.thermal_area_margin)


def evaluate_subsystems(inputs: SubsystemInputs | None = None) -> SubsystemResult:
    inputs = inputs or SubsystemInputs()
    average_power, array_power, array_area, battery = power_sizing(inputs)
    ebn0, link_margin = xband_link_budget(inputs)
    min_torque, wheel_torque, min_momentum, wheel_momentum = adcs_sizing(inputs)
    delta_v, propellant = propulsion_sizing(inputs)
    radiator = thermal_sizing(inputs)
    dry_mass = sum(MASS_BUDGET_KG.values())
    wet_with_margin = dry_mass * 1.15 + propellant
    return SubsystemResult(
        orbital_period_min(inputs.altitude_km), average_power, array_power,
        array_area, battery, ebn0, link_margin, min_torque, wheel_torque,
        min_momentum, wheel_momentum, delta_v, propellant, radiator, dry_mass,
        wet_with_margin, inputs.wet_mass_limit_kg - wet_with_margin,
    )


def write_csv(result: SubsystemResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream); writer.writerow(["metric", "value"])
        writer.writerows(asdict(result).items())


def plot_budgets(result: SubsystemResult, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(list(MASS_BUDGET_KG), list(MASS_BUDGET_KG.values()))
    ax.set(title="Preliminary subsystem mass allocation", xlabel="Mass per spacecraft [kg]")
    ax.grid(axis="x", alpha=0.3); fig.tight_layout(); fig.savefig(output / "subsystem_mass_budget.png", dpi=200); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.5))
    axes[0].bar(["Average load", "Required EOL array"], [result.average_operational_power_w, result.required_eol_array_power_w])
    axes[0].set(ylabel="Power [W]", title="Electrical-power sizing"); axes[0].grid(axis="y", alpha=0.3)
    axes[1].bar(["Required", "Available"], [8.0, result.link_ebn0_db])
    axes[1].set(ylabel="Eb/N0 [dB]", title=f"X-band margin = {result.link_margin_db:.1f} dB"); axes[1].grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(output / "power_and_link_closure.png", dpi=200); plt.close(fig)


def main() -> None:
    root = Path(__file__).resolve().parent
    output = root / "results" / "spacecraft_subsystems"
    result = evaluate_subsystems(); write_csv(result, output / "subsystem_sizing.csv"); plot_budgets(result, output)
    print("PHASE 6 PRELIMINARY SPACECRAFT SUBSYSTEM SIZING")
    print("Concept estimates only - component and environment validation remain.")
    for key, value in asdict(result).items(): print(f"{key}: {value}")


if __name__ == "__main__": main()
