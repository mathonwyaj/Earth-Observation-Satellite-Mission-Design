"""Preliminary multispectral Earth-observation payload sizing.

The model intentionally uses transparent first-order equations. It is intended
for early trade studies; later phases will add Earth curvature, off-nadir
imaging, detector MTF, optical losses, SNR, and detailed image-motion models.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, asdict
from pathlib import Path

import matplotlib.pyplot as plt


EARTH_MU = 3.986004418e14  # m^3/s^2
EARTH_RADIUS = 6_378_137.0  # m


@dataclass(frozen=True)
class PayloadDesign:
    altitude_km: float
    pixel_pitch_um: float
    cross_track_pixels: int
    target_gsd_m: float
    wavelength_nm: float = 850.0
    smear_limit_pixels: float = 0.5


@dataclass(frozen=True)
class PayloadResult:
    altitude_km: float
    pixel_pitch_um: float
    cross_track_pixels: int
    focal_length_mm: float
    sensor_width_mm: float
    field_of_view_deg: float
    swath_width_km: float
    diffraction_aperture_mm: float
    f_number: float
    orbital_speed_km_s: float
    maximum_exposure_ms: float
    meets_50_km_swath: bool


def size_payload(design: PayloadDesign) -> PayloadResult:
    """Return first-order optical and smear sizing for a nadir imager."""
    altitude_m = design.altitude_km * 1_000.0
    pixel_pitch_m = design.pixel_pitch_um * 1e-6
    wavelength_m = design.wavelength_nm * 1e-9

    # Nadir pinhole-camera relation: GSD = H * p / f.
    focal_length_m = altitude_m * pixel_pitch_m / design.target_gsd_m
    sensor_width_m = design.cross_track_pixels * pixel_pitch_m
    field_of_view_rad = 2.0 * math.atan(sensor_width_m / (2.0 * focal_length_m))
    swath_width_m = 2.0 * altitude_m * math.tan(field_of_view_rad / 2.0)

    # Rayleigh angular resolution mapped to the requested ground sample.
    aperture_m = 1.22 * wavelength_m * altitude_m / design.target_gsd_m
    f_number = focal_length_m / aperture_m

    orbital_speed_m_s = math.sqrt(
        EARTH_MU / (EARTH_RADIUS + altitude_m)
    )
    maximum_exposure_s = (
        design.smear_limit_pixels * design.target_gsd_m / orbital_speed_m_s
    )

    return PayloadResult(
        altitude_km=design.altitude_km,
        pixel_pitch_um=design.pixel_pitch_um,
        cross_track_pixels=design.cross_track_pixels,
        focal_length_mm=focal_length_m * 1_000.0,
        sensor_width_mm=sensor_width_m * 1_000.0,
        field_of_view_deg=math.degrees(field_of_view_rad),
        swath_width_km=swath_width_m / 1_000.0,
        diffraction_aperture_mm=aperture_m * 1_000.0,
        f_number=f_number,
        orbital_speed_km_s=orbital_speed_m_s / 1_000.0,
        maximum_exposure_ms=maximum_exposure_s * 1_000.0,
        meets_50_km_swath=swath_width_m >= 50_000.0,
    )


def generate_trade() -> list[PayloadResult]:
    altitudes_km = [450, 500, 550, 600, 650]
    pixel_pitches_um = [5.5, 7.0, 10.0, 12.0]
    pixel_counts = [4096, 6144, 8192]
    return [
        size_payload(PayloadDesign(h, pitch, pixels, target_gsd_m=10.0))
        for h in altitudes_km
        for pitch in pixel_pitches_um
        for pixels in pixel_counts
    ]


def write_csv(results: list[PayloadResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def plot_focal_length(results: list[PayloadResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    for pitch in sorted({r.pixel_pitch_um for r in results}):
        subset = [
            r for r in results
            if r.pixel_pitch_um == pitch and r.cross_track_pixels == 8192
        ]
        ax.plot(
            [r.altitude_km for r in subset],
            [r.focal_length_mm for r in subset],
            marker="o",
            label=f"{pitch:g} um pixels",
        )
    ax.set(
        title="Focal length required for 10 m GSD",
        xlabel="Orbit altitude [km]",
        ylabel="Required focal length [mm]",
    )
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_detector_trade(results: list[PayloadResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_altitude = 550
    baseline_pitch = 10.0
    subset = [
        r for r in results
        if r.altitude_km == baseline_altitude
        and r.pixel_pitch_um == baseline_pitch
    ]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(
        [str(r.cross_track_pixels) for r in subset],
        [r.swath_width_km for r in subset],
        color=["#8da0cb", "#66c2a5", "#fc8d62"],
    )
    ax.axhline(50.0, color="black", linestyle="--", label="50 km requirement")
    ax.set(
        title="Detector width trade at 550 km and 10 m GSD",
        xlabel="Cross-track pixels",
        ylabel="Swath width [km]",
    )
    ax.grid(axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def main() -> None:
    root = Path(__file__).resolve().parent
    output = root / "results" / "payload"
    results = generate_trade()
    write_csv(results, output / "payload_trade.csv")
    plot_focal_length(results, output / "focal_length_trade.jpg")
    plot_detector_trade(results, output / "detector_swath_trade.jpg")

    baseline = size_payload(
        PayloadDesign(
            altitude_km=550,
            pixel_pitch_um=10.0,
            cross_track_pixels=8192,
            target_gsd_m=10.0,
        )
    )
    print("PRELIMINARY BASELINE - NOT A FINAL DESIGN")
    for key, value in asdict(baseline).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
