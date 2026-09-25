"""Phase 3 constrained payload optimisation.

The preferred design is selected using the conservative Phase 2 detector and
throughput assumptions. Enhanced-detector cases are retained as sensitivity
studies and are not used to claim baseline compliance.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt

from payload_radiometry import BANDS, RadiometryInputs, band_radiometry
from payload_sizing import PayloadDesign, size_payload


SNR_REQUIREMENT = 50.0


@dataclass(frozen=True)
class DetectorScenario:
    name: str
    throughput: float
    quantum_efficiency: float


@dataclass(frozen=True)
class OptimisationResult:
    scenario: str
    aperture_mm: float
    exposure_ms: float
    minimum_band_snr: float
    limiting_band: str
    blue_snr: float
    green_snr: float
    red_snr: float
    nir_snr: float
    f_number: float
    estimated_payload_mass_kg: float
    estimated_telescope_envelope_l: float
    smear_pixels: float
    meets_snr: bool
    meets_smear: bool
    meets_diffraction: bool
    feasible: bool


STANDARD = DetectorScenario("Standard", throughput=0.35, quantum_efficiency=0.60)
ENHANCED = DetectorScenario("Enhanced sensitivity", throughput=0.45, quantum_efficiency=0.75)


def estimate_payload_resources(aperture_mm: float, focal_length_mm: float) -> tuple[float, float]:
    """Return parametric mass and envelope estimates for concept comparison.

    These are design heuristics, not CAD-derived or vendor-qualified values.
    They are deliberately reported as estimates and will be replaced by the
    later mechanical configuration and structural model.
    """
    mass_kg = 1.5 + 2.2 * (aperture_mm / 100.0) ** 2 + 0.8 * (focal_length_mm / 550.0)
    diameter_m = (aperture_mm + 40.0) / 1_000.0
    length_m = 0.65  # folded/telephoto concept envelope assumption
    envelope_l = diameter_m**2 * length_m * 1_000.0
    return mass_kg, envelope_l


def evaluate_candidate(
    design: PayloadDesign,
    scenario: DetectorScenario,
    aperture_mm: float,
    exposure_ms: float,
) -> OptimisationResult:
    geometry = size_payload(design)
    inputs = RadiometryInputs(
        aperture_mm=aperture_mm,
        throughput=scenario.throughput,
        quantum_efficiency=scenario.quantum_efficiency,
        exposure_ms=exposure_ms,
    )
    band_results = [band_radiometry(band, design, inputs) for band in BANDS]
    snrs = {result.band: result.snr for result in band_results}
    limiting_band = min(snrs, key=snrs.get)
    minimum_snr = snrs[limiting_band]
    smear_pixels = exposure_ms / geometry.maximum_exposure_ms * design.smear_limit_pixels
    mass_kg, envelope_l = estimate_payload_resources(aperture_mm, geometry.focal_length_mm)
    meets_snr = minimum_snr >= SNR_REQUIREMENT
    meets_smear = smear_pixels <= design.smear_limit_pixels + 1e-12
    meets_diffraction = aperture_mm >= geometry.diffraction_aperture_mm
    return OptimisationResult(
        scenario=scenario.name,
        aperture_mm=aperture_mm,
        exposure_ms=exposure_ms,
        minimum_band_snr=minimum_snr,
        limiting_band=limiting_band,
        blue_snr=snrs["Blue"],
        green_snr=snrs["Green"],
        red_snr=snrs["Red"],
        nir_snr=snrs["NIR"],
        f_number=geometry.focal_length_mm / aperture_mm,
        estimated_payload_mass_kg=mass_kg,
        estimated_telescope_envelope_l=envelope_l,
        smear_pixels=smear_pixels,
        meets_snr=meets_snr,
        meets_smear=meets_smear,
        meets_diffraction=meets_diffraction,
        feasible=meets_snr and meets_smear and meets_diffraction,
    )


def generate_trade(design: PayloadDesign) -> list[OptimisationResult]:
    apertures = range(80, 201, 5)
    exposures_ms = (0.30, 0.45, 0.60, 0.65)
    return [
        evaluate_candidate(design, scenario, aperture, exposure)
        for scenario in (STANDARD, ENHANCED)
        for aperture in apertures
        for exposure in exposures_ms
    ]


def select_preferred(results: list[OptimisationResult]) -> OptimisationResult:
    """Select the lightest feasible standard-technology candidate."""
    feasible = [r for r in results if r.scenario == STANDARD.name and r.feasible]
    if not feasible:
        raise RuntimeError("No feasible standard-technology design in search range")
    return min(
        feasible,
        key=lambda r: (r.estimated_payload_mass_kg, -r.minimum_band_snr, r.exposure_ms),
    )


def write_csv(results: list[OptimisationResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(result) for result in results)


def plot_aperture_sensitivity(results: list[OptimisationResult], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for scenario in (STANDARD.name, ENHANCED.name):
        subset = [
            r for r in results
            if r.scenario == scenario and r.exposure_ms == 0.65
        ]
        ax.plot(
            [r.aperture_mm for r in subset],
            [r.minimum_band_snr for r in subset],
            marker="o",
            markersize=3,
            label=scenario,
        )
    ax.axhline(SNR_REQUIREMENT, color="black", linestyle="--", label="SNR requirement")
    ax.set(title="Worst-band SNR versus aperture at 0.65 ms",
           xlabel="Clear aperture [mm]", ylabel="Minimum band SNR")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_mass_performance(results: list[OptimisationResult], preferred: OptimisationResult, path: Path) -> None:
    subset = [
        r for r in results
        if r.scenario == STANDARD.name and r.exposure_ms == 0.65
    ]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(
        [r.estimated_payload_mass_kg for r in subset],
        [r.minimum_band_snr for r in subset],
        marker="o",
        markersize=3,
    )
    ax.scatter([preferred.estimated_payload_mass_kg], [preferred.minimum_band_snr],
               color="#d00000", s=70, zorder=3, label="Preferred baseline")
    ax.axhline(SNR_REQUIREMENT, color="black", linestyle="--")
    ax.set(title="Parametric payload mass versus worst-band SNR",
           xlabel="Estimated payload mass [kg]", ylabel="Minimum band SNR")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main() -> None:
    root = Path(__file__).resolve().parent
    output = root / "results" / "optimisation"
    output.mkdir(parents=True, exist_ok=True)
    design = PayloadDesign(550.0, 10.0, 8192, 10.0)
    results = generate_trade(design)
    preferred = select_preferred(results)
    write_csv(results, output / "payload_optimisation_trade.csv")
    plot_aperture_sensitivity(results, output / "aperture_snr_optimisation.png")
    plot_mass_performance(results, preferred, output / "mass_snr_trade.png")

    print("PHASE 3 PREFERRED PRELIMINARY PAYLOAD")
    print("Selection uses conservative standard detector assumptions.")
    for key, value in asdict(preferred).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
