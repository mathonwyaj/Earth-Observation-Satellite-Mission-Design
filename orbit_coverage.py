"""Phase 4 sun-synchronous orbit and preliminary UK revisit analysis.

The propagator assumes a circular orbit, secular J2 RAAN drift and a spherical
rotating Earth. Revisit is evaluated at representative UK sites; it is not yet
a full land-area coverage certification.
"""

from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from payload_sizing import EARTH_MU, EARTH_RADIUS, PayloadDesign, size_payload


J2 = 1.08262668e-3
EARTH_ROTATION = 7.2921150e-5  # rad/s
TROPICAL_YEAR_S = 365.2422 * 86400.0
SUN_SYNCHRONOUS_RATE = 2.0 * math.pi / TROPICAL_YEAR_S

UK_SITES = {
    "London": (51.5074, -0.1278),
    "Cardiff": (51.4816, -3.1791),
    "Manchester": (53.4808, -2.2426),
    "Edinburgh": (55.9533, -3.1883),
    "Belfast": (54.5973, -5.9301),
}


@dataclass(frozen=True)
class OrbitCase:
    altitude_km: float
    off_nadir_deg: float
    swath_km: float = 81.92
    constellation_size: int = 1


@dataclass(frozen=True)
class OrbitTradeResult:
    altitude_km: float
    inclination_deg: float
    off_nadir_deg: float
    constellation_size: int
    orbital_period_min: float
    coverage_half_width_km: float
    london_max_revisit_h: float
    cardiff_max_revisit_h: float
    manchester_max_revisit_h: float
    edinburgh_max_revisit_h: float
    belfast_max_revisit_h: float
    worst_site_max_revisit_h: float
    mean_site_revisit_h: float
    sites_with_two_or_more_accesses: int
    meets_48_h_representative_site_target: bool


def sun_synchronous_inclination_deg(altitude_km: float) -> float:
    """Return circular-orbit inclination giving the mean solar RAAN rate."""
    radius_m = EARTH_RADIUS + altitude_km * 1_000.0
    mean_motion = math.sqrt(EARTH_MU / radius_m**3)
    denominator = 1.5 * J2 * mean_motion * (EARTH_RADIUS / radius_m) ** 2
    cos_i = -SUN_SYNCHRONOUS_RATE / denominator
    if abs(cos_i) > 1.0:
        raise ValueError("No circular sun-synchronous solution at this altitude")
    return math.degrees(math.acos(cos_i))


def orbital_period_min(altitude_km: float) -> float:
    radius_m = EARTH_RADIUS + altitude_km * 1_000.0
    return 2.0 * math.pi * math.sqrt(radius_m**3 / EARTH_MU) / 60.0


def coverage_half_angle_rad(
    altitude_km: float,
    swath_km: float,
    off_nadir_deg: float,
) -> float:
    """Return Earth-centred coverage half-angle including payload roll agility."""
    radius_m = EARTH_RADIUS + altitude_km * 1_000.0
    # The nadir swath defines the instrument half field angle at this altitude.
    half_fov_rad = math.atan((swath_km * 500.0) / (altitude_km * 1_000.0))
    look_rad = math.radians(off_nadir_deg) + half_fov_rad
    horizon_look_rad = math.asin(EARTH_RADIUS / radius_m)
    if look_rad >= horizon_look_rad:
        raise ValueError("Requested look angle reaches or exceeds the horizon")
    slant_m = (
        radius_m * math.cos(look_rad)
        - math.sqrt(EARTH_RADIUS**2 - radius_m**2 * math.sin(look_rad) ** 2)
    )
    return math.atan2(
        slant_m * math.sin(look_rad),
        radius_m - slant_m * math.cos(look_rad),
    )


def propagate_ground_track(
    altitude_km: float,
    duration_days: float,
    step_s: float,
    initial_raan_deg: float = 0.0,
    initial_argument_deg: float = 0.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Propagate latitude/longitude using circular motion and secular J2 RAAN."""
    radius_m = EARTH_RADIUS + altitude_km * 1_000.0
    inclination = math.radians(sun_synchronous_inclination_deg(altitude_km))
    mean_motion = math.sqrt(EARTH_MU / radius_m**3)
    times = np.arange(0.0, duration_days * 86400.0 + 0.5 * step_s, step_s)
    argument = mean_motion * times + math.radians(initial_argument_deg)
    raan = math.radians(initial_raan_deg) + SUN_SYNCHRONOUS_RATE * times

    cos_o, sin_o = np.cos(raan), np.sin(raan)
    cos_u, sin_u = np.cos(argument), np.sin(argument)
    cos_i, sin_i = math.cos(inclination), math.sin(inclination)
    x_eci = radius_m * (cos_o * cos_u - sin_o * sin_u * cos_i)
    y_eci = radius_m * (sin_o * cos_u + cos_o * sin_u * cos_i)
    z_eci = radius_m * sin_u * sin_i

    earth_angle = EARTH_ROTATION * times
    x_ecef = np.cos(earth_angle) * x_eci + np.sin(earth_angle) * y_eci
    y_ecef = -np.sin(earth_angle) * x_eci + np.cos(earth_angle) * y_eci
    latitude = np.degrees(np.arcsin(z_eci / radius_m))
    longitude = np.degrees(np.arctan2(y_ecef, x_ecef))
    return times, latitude, longitude


def angular_separation_rad(
    latitude_deg: np.ndarray,
    longitude_deg: np.ndarray,
    target_lat_deg: float,
    target_lon_deg: float,
) -> np.ndarray:
    lat = np.radians(latitude_deg)
    lon = np.radians(longitude_deg)
    target_lat = math.radians(target_lat_deg)
    target_lon = math.radians(target_lon_deg)
    cosine = (
        np.sin(lat) * math.sin(target_lat)
        + np.cos(lat) * math.cos(target_lat) * np.cos(lon - target_lon)
    )
    return np.arccos(np.clip(cosine, -1.0, 1.0))


def access_event_times(times: np.ndarray, access: np.ndarray) -> np.ndarray:
    """Collapse consecutive in-view samples into one mid-access timestamp."""
    indices = np.flatnonzero(access)
    if indices.size == 0:
        return np.array([], dtype=float)
    splits = np.where(np.diff(indices) > 1)[0] + 1
    groups = np.split(indices, splits)
    return np.array([times[group[len(group) // 2]] for group in groups])


def site_max_revisit_hours(
    times: np.ndarray,
    latitudes_deg: np.ndarray,
    longitudes_deg: np.ndarray,
    target: tuple[float, float],
    coverage_half_angle: float,
) -> tuple[float, int]:
    separation = angular_separation_rad(
        latitudes_deg, longitudes_deg, target[0], target[1]
    )
    events = access_event_times(times, separation <= coverage_half_angle)
    if len(events) < 2:
        return math.inf, len(events)
    return float(np.max(np.diff(events)) / 3600.0), len(events)


def evaluate_case(
    case: OrbitCase,
    duration_days: float = 20.0,
    step_s: float = 20.0,
) -> OrbitTradeResult:
    if case.constellation_size < 1:
        raise ValueError("Constellation size must be at least one")
    tracks = [
        propagate_ground_track(
            case.altitude_km,
            duration_days,
            step_s,
            initial_argument_deg=360.0 * member / case.constellation_size,
        )
        for member in range(case.constellation_size)
    ]
    times = tracks[0][0]
    half_angle = coverage_half_angle_rad(
        case.altitude_km, case.swath_km, case.off_nadir_deg
    )
    revisits: dict[str, float] = {}
    counts: dict[str, int] = {}
    for name, target in UK_SITES.items():
        combined_access = np.zeros_like(times, dtype=bool)
        for _, latitudes, longitudes in tracks:
            combined_access |= (
                angular_separation_rad(
                    latitudes, longitudes, target[0], target[1]
                )
                <= half_angle
            )
        events = access_event_times(times, combined_access)
        if len(events) < 2:
            revisits[name], counts[name] = math.inf, len(events)
        else:
            revisits[name] = float(np.max(np.diff(events)) / 3600.0)
            counts[name] = len(events)
    finite = [value for value in revisits.values() if math.isfinite(value)]
    worst = max(revisits.values())
    mean = sum(finite) / len(finite) if finite else math.inf
    return OrbitTradeResult(
        altitude_km=case.altitude_km,
        inclination_deg=sun_synchronous_inclination_deg(case.altitude_km),
        off_nadir_deg=case.off_nadir_deg,
        constellation_size=case.constellation_size,
        orbital_period_min=orbital_period_min(case.altitude_km),
        coverage_half_width_km=half_angle * EARTH_RADIUS / 1_000.0,
        london_max_revisit_h=revisits["London"],
        cardiff_max_revisit_h=revisits["Cardiff"],
        manchester_max_revisit_h=revisits["Manchester"],
        edinburgh_max_revisit_h=revisits["Edinburgh"],
        belfast_max_revisit_h=revisits["Belfast"],
        worst_site_max_revisit_h=worst,
        mean_site_revisit_h=mean,
        sites_with_two_or_more_accesses=sum(count >= 2 for count in counts.values()),
        meets_48_h_representative_site_target=worst <= 48.0,
    )


def generate_trade() -> list[OrbitTradeResult]:
    return [
        evaluate_case(
            OrbitCase(
                altitude_km=altitude,
                off_nadir_deg=off_nadir,
                constellation_size=constellation_size,
            )
        )
        for altitude in (450.0, 500.0, 550.0, 600.0, 650.0)
        for off_nadir in (0.0, 15.0, 25.0)
        for constellation_size in (1, 2)
    ]


def select_preferred(results: list[OrbitTradeResult]) -> OrbitTradeResult:
    feasible = [r for r in results if r.meets_48_h_representative_site_target]
    if not feasible:
        # Preserve an honest best-available result if the target is not met.
        return min(results, key=lambda r: r.worst_site_max_revisit_h)
    return min(
        feasible,
        key=lambda r: (
            r.constellation_size,
            abs(r.altitude_km - 550.0),
            r.off_nadir_deg,
            r.worst_site_max_revisit_h,
        ),
    )


def write_csv(results: list[OrbitTradeResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(result) for result in results)


def plot_revisit_trade(results: list[OrbitTradeResult], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    styles = {1: "--", 2: "-"}
    for constellation_size in (1, 2):
      for off_nadir in (0.0, 15.0, 25.0):
        subset = [r for r in results if r.off_nadir_deg == off_nadir]
        subset = [r for r in subset if r.constellation_size == constellation_size]
        values = [
            r.worst_site_max_revisit_h if math.isfinite(r.worst_site_max_revisit_h) else 500.0
            for r in subset
        ]
        ax.plot([r.altitude_km for r in subset], values, marker="o",
                linestyle=styles[constellation_size],
                label=f"{constellation_size} sat, ±{off_nadir:g}°")
    ax.axhline(48.0, color="black", linestyle="--", label="48 h target")
    ax.set(title="Representative UK-site maximum revisit trade",
           xlabel="Orbit altitude [km]", ylabel="Worst-site maximum revisit [h]")
    ax.set_ylim(0, 168)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_ground_track(preferred: OrbitTradeResult, path: Path) -> None:
    times, latitudes, longitudes = propagate_ground_track(
        preferred.altitude_km, duration_days=1.0, step_s=30.0
    )
    del times
    fig, ax = plt.subplots(figsize=(10, 5.5))
    jumps = np.where(np.abs(np.diff(longitudes)) > 180.0)[0] + 1
    for segment in np.split(np.arange(len(longitudes)), jumps):
        ax.plot(longitudes[segment], latitudes[segment], linewidth=0.8, color="#277da1")
    for name, (lat, lon) in UK_SITES.items():
        ax.scatter(lon, lat, s=30, color="#d00000")
        ax.text(lon + 1.0, lat + 0.4, name, fontsize=8)
    ax.axvspan(-8.5, 2.0, ymin=(49.5 + 90) / 180, ymax=(59.5 + 90) / 180,
               color="#90be6d", alpha=0.15, label="UK analysis box")
    ax.set(xlim=(-180, 180), ylim=(-90, 90), xlabel="Longitude [deg]",
           ylabel="Latitude [deg]",
           title=(f"One-day lead-satellite SSO ground track: "
                  f"{preferred.altitude_km:.0f} km"))
    ax.grid(alpha=0.3)
    ax.legend(loc="lower left")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main() -> None:
    root = Path(__file__).resolve().parent
    output = root / "results" / "orbit_coverage"
    output.mkdir(parents=True, exist_ok=True)
    results = generate_trade()
    preferred = select_preferred(results)
    write_csv(results, output / "orbit_coverage_trade.csv")
    plot_revisit_trade(results, output / "uk_revisit_trade.png")
    plot_ground_track(preferred, output / "preferred_ground_track.png")
    print("PHASE 4 PRELIMINARY ORBIT AND COVERAGE RESULT")
    print("Revisit is for five representative UK sites, not a complete UK area mask.")
    for key, value in asdict(preferred).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
