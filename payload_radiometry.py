"""Phase 2 multispectral radiometry and data-budget model.

This is a transparent first-order engineering model for concept trades. Solar
irradiance, reflectance, throughput and detector-noise values are assumptions,
not vendor-qualified performance data.
"""

from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt

from payload_sizing import PayloadDesign, size_payload


PLANCK = 6.62607015e-34  # J s
LIGHT_SPEED = 299_792_458.0  # m/s


@dataclass(frozen=True)
class SpectralBand:
    name: str
    centre_nm: float
    bandwidth_nm: float
    solar_irradiance_w_m2_nm: float
    design_reflectance: float


@dataclass(frozen=True)
class RadiometryInputs:
    aperture_mm: float = 80.0
    throughput: float = 0.35
    quantum_efficiency: float = 0.60
    exposure_ms: float = 0.60
    read_noise_e: float = 12.0
    dark_current_e_s: float = 50.0
    bits_per_pixel: int = 12
    compression_ratio: float = 4.0
    along_track_scene_km: float = 1_000.0


@dataclass(frozen=True)
class BandResult:
    band: str
    centre_nm: float
    bandwidth_nm: float
    design_reflectance: float
    signal_electrons: float
    shot_noise_e: float
    total_noise_e: float
    snr: float


@dataclass(frozen=True)
class DataBudget:
    line_rate_hz: float
    raw_data_rate_mbps: float
    compressed_data_rate_mbps: float
    scene_duration_s: float
    raw_scene_gbit: float
    compressed_scene_gbit: float
    downlink_time_at_150_mbps_s: float


BANDS = (
    SpectralBand("Blue", 490.0, 65.0, 1.93, 0.05),
    SpectralBand("Green", 560.0, 35.0, 1.84, 0.08),
    SpectralBand("Red", 665.0, 30.0, 1.55, 0.06),
    SpectralBand("NIR", 842.0, 115.0, 1.03, 0.02),
)


def band_radiometry(
    band: SpectralBand,
    design: PayloadDesign,
    inputs: RadiometryInputs,
) -> BandResult:
    """Estimate signal electrons and photon/read/dark-noise-limited SNR."""
    geometry = size_payload(design)
    aperture_area_m2 = math.pi * (inputs.aperture_mm * 1e-3) ** 2 / 4.0
    focal_length_m = geometry.focal_length_mm * 1e-3
    pixel_pitch_m = design.pixel_pitch_um * 1e-6
    pixel_solid_angle_sr = (pixel_pitch_m / focal_length_m) ** 2

    # Lambertian target: L_lambda = E_sun * reflectance / pi.
    radiance_w_m2_sr_nm = (
        band.solar_irradiance_w_m2_nm * band.design_reflectance / math.pi
    )
    optical_power_w = (
        radiance_w_m2_sr_nm
        * band.bandwidth_nm
        * aperture_area_m2
        * pixel_solid_angle_sr
        * inputs.throughput
    )
    exposure_s = inputs.exposure_ms * 1e-3
    photon_energy_j = PLANCK * LIGHT_SPEED / (band.centre_nm * 1e-9)
    signal_e = optical_power_w * exposure_s / photon_energy_j * inputs.quantum_efficiency
    dark_e = inputs.dark_current_e_s * exposure_s
    shot_noise_e = math.sqrt(signal_e)
    total_noise_e = math.sqrt(signal_e + dark_e + inputs.read_noise_e**2)
    return BandResult(
        band=band.name,
        centre_nm=band.centre_nm,
        bandwidth_nm=band.bandwidth_nm,
        design_reflectance=band.design_reflectance,
        signal_electrons=signal_e,
        shot_noise_e=shot_noise_e,
        total_noise_e=total_noise_e,
        snr=signal_e / total_noise_e,
    )


def calculate_data_budget(
    design: PayloadDesign,
    inputs: RadiometryInputs,
    number_of_bands: int,
    downlink_mbps: float = 150.0,
) -> DataBudget:
    geometry = size_payload(design)
    line_rate_hz = geometry.orbital_speed_km_s * 1_000.0 / design.target_gsd_m
    raw_bps = (
        design.cross_track_pixels
        * number_of_bands
        * inputs.bits_per_pixel
        * line_rate_hz
    )
    compressed_bps = raw_bps / inputs.compression_ratio
    scene_duration_s = inputs.along_track_scene_km / geometry.orbital_speed_km_s
    raw_scene_bits = raw_bps * scene_duration_s
    compressed_scene_bits = compressed_bps * scene_duration_s
    return DataBudget(
        line_rate_hz=line_rate_hz,
        raw_data_rate_mbps=raw_bps / 1e6,
        compressed_data_rate_mbps=compressed_bps / 1e6,
        scene_duration_s=scene_duration_s,
        raw_scene_gbit=raw_scene_bits / 1e9,
        compressed_scene_gbit=compressed_scene_bits / 1e9,
        downlink_time_at_150_mbps_s=compressed_scene_bits / (downlink_mbps * 1e6),
    )


def aperture_trade(
    design: PayloadDesign,
    base_inputs: RadiometryInputs,
    apertures_mm: list[float],
) -> dict[str, list[float]]:
    return {
        band.name: [
            band_radiometry(
                band,
                design,
                RadiometryInputs(**{**asdict(base_inputs), "aperture_mm": aperture}),
            ).snr
            for aperture in apertures_mm
        ]
        for band in BANDS
    }


def write_band_csv(results: list[BandResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(result) for result in results)


def plot_snr(results: list[BandResult], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.bar([r.band for r in results], [r.snr for r in results], color="#277da1")
    ax.axhline(50.0, color="#d00000", linestyle="--", label="Provisional SNR target")
    ax.set(title="Baseline SNR under dark-water design reflectance",
           xlabel="Spectral band", ylabel="Estimated SNR")
    ax.grid(axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_aperture_trade(design: PayloadDesign, inputs: RadiometryInputs, path: Path) -> None:
    apertures = list(range(50, 131, 10))
    trade = aperture_trade(design, inputs, apertures)
    fig, ax = plt.subplots(figsize=(8, 5))
    for band, snr_values in trade.items():
        ax.plot(apertures, snr_values, marker="o", label=band)
    ax.axhline(50.0, color="black", linestyle="--", label="Provisional SNR target")
    ax.set(title="Aperture-to-SNR trade", xlabel="Clear aperture [mm]",
           ylabel="Estimated SNR")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main() -> None:
    root = Path(__file__).resolve().parent
    output = root / "results" / "radiometry"
    output.mkdir(parents=True, exist_ok=True)
    design = PayloadDesign(550.0, 10.0, 8192, 10.0)
    inputs = RadiometryInputs()
    results = [band_radiometry(band, design, inputs) for band in BANDS]
    data = calculate_data_budget(design, inputs, len(BANDS))

    write_band_csv(results, output / "band_radiometry.csv")
    plot_snr(results, output / "baseline_band_snr.png")
    plot_aperture_trade(design, inputs, output / "aperture_snr_trade.png")

    print("PHASE 2 PRELIMINARY RADIOMETRY - NOT FLIGHT-QUALIFIED PERFORMANCE")
    print(f"Aperture: {inputs.aperture_mm:.1f} mm")
    print(f"Exposure: {inputs.exposure_ms:.3f} ms")
    for result in results:
        print(f"{result.band:>5}: SNR={result.snr:7.2f}, signal={result.signal_electrons:10.1f} e-")
    print("\nDATA BUDGET")
    for key, value in asdict(data).items():
        print(f"{key}: {value:.3f}")


if __name__ == "__main__":
    main()
