"""Phase 5 preliminary mission-operations, storage and downlink analysis.

This concept model links the Phase 2 image volume to first-order ground-station
access geometry. It is an engineering trade study, not a licensed-station pass
schedule or a detailed RF link budget.
"""

from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from orbit_coverage import EARTH_ROTATION, SUN_SYNCHRONOUS_RATE, orbital_period_min, sun_synchronous_inclination_deg
from payload_radiometry import BANDS, RadiometryInputs, calculate_data_budget
from payload_sizing import EARTH_MU, EARTH_RADIUS, PayloadDesign

GROUND_STATIONS = {"Goonhilly": (50.05, -5.18), "Svalbard": (78.23, 15.41)}


@dataclass(frozen=True)
class OperationsInputs:
    altitude_km: float = 550.0
    constellation_size: int = 2
    duration_days: float = 7.0
    step_s: float = 10.0
    minimum_elevation_deg: float = 10.0
    downlink_mbps: float = 150.0
    link_efficiency: float = 0.70
    station_availability: float = 0.90
    scenes_per_day_per_spacecraft: int = 4
    storage_margin: float = 0.20


@dataclass(frozen=True)
class NetworkResult:
    network: str
    stations: int
    passes_per_spacecraft_per_day: float
    mean_pass_duration_min: float
    daily_downlink_capacity_gbit_per_spacecraft: float
    daily_generated_data_gbit_per_spacecraft: float
    capacity_margin_percent: float
    peak_backlog_gbit_per_spacecraft: float
    recommended_storage_gb_per_spacecraft: float
    worst_priority_latency_h: float
    meets_daily_capacity: bool
    meets_three_hour_priority_target: bool


def station_central_angle_limit_rad(altitude_km: float, elevation_deg: float) -> float:
    """Maximum geocentric separation for visibility above an elevation mask."""
    radius = EARTH_RADIUS + altitude_km * 1_000.0
    elevation = math.radians(elevation_deg)
    return math.acos(EARTH_RADIUS / radius * math.cos(elevation)) - elevation


def angular_separation_rad(latitude_deg, longitude_deg, target_lat_deg, target_lon_deg):
    lat, lon = np.radians(latitude_deg), np.radians(longitude_deg)
    target_lat, target_lon = math.radians(target_lat_deg), math.radians(target_lon_deg)
    cosine = np.sin(lat) * math.sin(target_lat) + np.cos(lat) * math.cos(target_lat) * np.cos(lon - target_lon)
    return np.arccos(np.clip(cosine, -1.0, 1.0))


def propagate_spacecraft(altitude_km, duration_days, step_s, phase_deg):
    radius = EARTH_RADIUS + altitude_km * 1_000.0
    inclination = math.radians(sun_synchronous_inclination_deg(altitude_km))
    mean_motion = math.sqrt(EARTH_MU / radius**3)
    times = np.arange(0.0, duration_days * 86400.0 + 0.5 * step_s, step_s)
    argument = mean_motion * times + math.radians(phase_deg)
    raan = SUN_SYNCHRONOUS_RATE * times
    x_eci = radius * (np.cos(raan) * np.cos(argument) - np.sin(raan) * np.sin(argument) * math.cos(inclination))
    y_eci = radius * (np.sin(raan) * np.cos(argument) + np.cos(raan) * np.sin(argument) * math.cos(inclination))
    z_eci = radius * np.sin(argument) * math.sin(inclination)
    earth_angle = EARTH_ROTATION * times
    x_ecef = np.cos(earth_angle) * x_eci + np.sin(earth_angle) * y_eci
    y_ecef = -np.sin(earth_angle) * x_eci + np.cos(earth_angle) * y_eci
    return times, np.degrees(np.arcsin(z_eci / radius)), np.degrees(np.arctan2(y_ecef, x_ecef))


def contact_windows(times, visible):
    indices = np.flatnonzero(visible)
    if indices.size == 0:
        return []
    groups = np.split(indices, np.where(np.diff(indices) > 1)[0] + 1)
    step = float(times[1] - times[0])
    return [(float(times[g[0]]), float(times[g[-1]] + step)) for g in groups]


def network_windows(times, latitudes, longitudes, station_names, inputs):
    visible = np.zeros_like(times, dtype=bool)
    limit = station_central_angle_limit_rad(inputs.altitude_km, inputs.minimum_elevation_deg)
    for station in station_names:
        latitude, longitude = GROUND_STATIONS[station]
        visible |= angular_separation_rad(latitudes, longitudes, latitude, longitude) <= limit
    return contact_windows(times, visible)


def acquisition_times(inputs):
    spacing = 86400.0 / inputs.scenes_per_day_per_spacecraft
    return np.arange(0.5 * spacing, inputs.duration_days * 86400.0, spacing)


def simulate_backlog(windows, acquisitions, scene_gbit, effective_rate_gbps):
    events = [(float(t), 1, scene_gbit) for t in acquisitions]
    events += [(start, 0, -effective_rate_gbps * (end - start)) for start, end in windows]
    backlog = peak = 0.0
    for _, kind, amount in sorted(events):
        backlog = max(0.0, backlog + amount) if kind == 0 else backlog + amount
        peak = max(peak, backlog)
    return peak, backlog


def worst_priority_latency_hours(windows, acquisitions, scene_gbit, effective_rate_gbps):
    transmit_s = scene_gbit / effective_rate_gbps
    latencies = []
    for acquisition in acquisitions:
        completion = math.inf
        for start, end in windows:
            if end <= acquisition:
                continue
            usable_start = max(start, float(acquisition))
            if end - usable_start >= transmit_s:
                completion = usable_start + transmit_s
                break
        latencies.append(completion - float(acquisition))
    return max(latencies) / 3600.0


def evaluate_network(network, station_names, inputs, scene_gbit):
    generated_daily = scene_gbit * inputs.scenes_per_day_per_spacecraft
    effective_rate = inputs.downlink_mbps / 1_000.0 * inputs.link_efficiency * inputs.station_availability
    spacecraft_results = []
    acquisitions = acquisition_times(inputs)
    for member in range(inputs.constellation_size):
        times, latitudes, longitudes = propagate_spacecraft(inputs.altitude_km, inputs.duration_days, inputs.step_s, 360.0 * member / inputs.constellation_size)
        windows = network_windows(times, latitudes, longitudes, station_names, inputs)
        contact_s = sum(end - start for start, end in windows)
        peak, _ = simulate_backlog(windows, acquisitions, scene_gbit, effective_rate)
        spacecraft_results.append({
            "passes": len(windows) / inputs.duration_days,
            "duration": contact_s / len(windows) / 60.0,
            "capacity": contact_s * effective_rate / inputs.duration_days,
            "peak": peak,
            "latency": worst_priority_latency_hours(windows, acquisitions, scene_gbit, effective_rate),
        })
    capacity = float(np.mean([x["capacity"] for x in spacecraft_results]))
    peak = max(x["peak"] for x in spacecraft_results)
    latency = max(x["latency"] for x in spacecraft_results)
    return NetworkResult(
        network, len(station_names),
        float(np.mean([x["passes"] for x in spacecraft_results])),
        float(np.mean([x["duration"] for x in spacecraft_results])),
        capacity, generated_daily, (capacity / generated_daily - 1.0) * 100.0,
        peak, peak * (1.0 + inputs.storage_margin) / 8.0, latency,
        capacity >= generated_daily, latency <= 3.0,
    )


def run_trade(inputs=None):
    inputs = inputs or OperationsInputs()
    data = calculate_data_budget(PayloadDesign(550.0, 10.0, 8192, 10.0), RadiometryInputs(), len(BANDS))
    networks = {"Goonhilly only": ("Goonhilly",), "Goonhilly + Svalbard": ("Goonhilly", "Svalbard")}
    return [evaluate_network(name, stations, inputs, data.compressed_scene_gbit) for name, stations in networks.items()]


def write_csv(results, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader(); writer.writerows(asdict(result) for result in results)


def plot_trade(results, path):
    labels = [r.network for r in results]; x = np.arange(len(results))
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.5))
    axes[0].bar(x - 0.18, [r.daily_generated_data_gbit_per_spacecraft for r in results], 0.36, label="Generated")
    axes[0].bar(x + 0.18, [r.daily_downlink_capacity_gbit_per_spacecraft for r in results], 0.36, label="Downlink capacity")
    axes[0].set(ylabel="Data per spacecraft [Gbit/day]", title="Daily data balance"); axes[0].set_xticks(x, labels, rotation=12); axes[0].legend(); axes[0].grid(axis="y", alpha=0.3)
    axes[1].bar(labels, [r.worst_priority_latency_h for r in results]); axes[1].axhline(3.0, color="red", linestyle="--", label="3 h target")
    axes[1].set(ylabel="Worst preliminary latency [h]", title="Priority delivery"); axes[1].tick_params(axis="x", rotation=12); axes[1].legend(); axes[1].grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)


def plot_contact_timeline(inputs, path):
    one_day = OperationsInputs(**{**asdict(inputs), "duration_days": 1.0})
    times, latitudes, longitudes = propagate_spacecraft(inputs.altitude_km, 1.0, inputs.step_s, 0.0)
    fig, ax = plt.subplots(figsize=(10, 3.5))
    for row, station in enumerate(GROUND_STATIONS):
        windows = network_windows(times, latitudes, longitudes, (station,), one_day)
        ax.broken_barh([(start / 3600.0, (end - start) / 3600.0) for start, end in windows], (row - 0.3, 0.6))
    ax.set(xlim=(0, 24), yticks=range(len(GROUND_STATIONS)), yticklabels=list(GROUND_STATIONS), xlabel="Mission elapsed time [h]", title="Representative first-day contacts — spacecraft 1")
    ax.grid(axis="x", alpha=0.3); fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)


def main():
    output = Path(__file__).resolve().parent / "results" / "mission_operations"; output.mkdir(parents=True, exist_ok=True)
    inputs = OperationsInputs(); results = run_trade(inputs)
    write_csv(results, output / "ground_network_trade.csv"); plot_trade(results, output / "data_latency_trade.png"); plot_contact_timeline(inputs, output / "contact_timeline.png")
    print("PHASE 5 PRELIMINARY MISSION OPERATIONS RESULT")
    print("Passes use idealised geometry and assumed station availability.")
    print(f"Orbit: {inputs.altitude_km:.0f} km, {orbital_period_min(inputs.altitude_km):.3f} min")
    print(f"Scenes/day/spacecraft: {inputs.scenes_per_day_per_spacecraft}")
    for result in results:
        print(f"\n{result.network}")
        for key, value in asdict(result).items():
            if key != "network": print(f"{key}: {value}")


if __name__ == "__main__":
    main()
