# Earth-Observation Satellite Mission & Systems Design

Preliminary design of a small multispectral satellite for UK flood monitoring.

## Project status

Phase 10 complete: final preliminary design review and evidence pack.

## Run the payload model

```bash
python payload_sizing.py
python payload_radiometry.py
python payload_optimisation.py
python orbit_coverage.py
python mission_operations.py
python spacecraft_subsystems.py
python integrated_budgets.py
python spacecraft_configuration.py
python monte_carlo_robustness.py
python final_design_review.py
```

Each script writes its trade results and figures to the corresponding folder
under `results/`.

## Run tests

```bash
python -m unittest discover -v
```

## Baseline requirements under assessment

- Ground-sampling distance: 10 m or better at nadir
- Swath width: at least 50 km
- Orbit-altitude trade range: 450-650 km
- Spectral range used for diffraction sizing: up to 850 nm
- Image-motion smear: no more than 0.5 pixel during exposure

These are preliminary design targets, not achieved performance claims.

## Phase 2 baseline assumptions

- Bands: blue, green, red and near-infrared (NIR)
- Clear aperture: 80 mm
- Optical throughput: 35 percent
- Detector quantum efficiency: 60 percent
- Exposure: 0.60 ms, below the Phase 1 smear limit
- Quantisation: 12 bits per pixel
- Lossless/near-lossless design compression assumption: 4:1
- Reference imaging strip: 1,000 km along track

The radiometric model uses assumed solar irradiance, dark-water reflectance and
detector noise. It is suitable for sensitivity studies but does not represent
validated vendor hardware or flight performance.

## Phase 3 optimisation

The optimiser searches aperture and exposure time while checking diffraction,
image smear and a provisional minimum SNR of 50 in every band. It compares a
standard detector baseline with an enhanced sensitivity case, but selects the
preferred design from the standard assumptions. Outputs are written to
`results/optimisation/`.

## Phase 4 orbit and coverage

The circular-orbit model calculates sun-synchronous inclination from J2 nodal
precession, propagates Earth-fixed ground tracks and estimates revisit for five
representative UK sites. It compares nadir, 15-degree and 25-degree off-nadir
access across 450-650 km and one- versus two-spacecraft architectures. Outputs
are written to `results/orbit_coverage/`.

## Phase 5 mission operations

The operations model compares Goonhilly-only and Goonhilly-plus-Svalbard
networks for the two-satellite 550 km architecture. It converts the Phase 2
compressed scene volume into daily generated data, geometric contacts, usable
downlink capacity, peak onboard backlog, recommended storage and preliminary
priority-delivery latency. Outputs are written to `results/mission_operations/`.

Ground-station coordinates, availability and protocol efficiency are explicit
concept-design assumptions. A later communications analysis must close the RF
link budget and validate real ground-service constraints.

## Phase 6 spacecraft subsystems

The subsystem model sizes solar-array and battery capacity, checks a preliminary
150 Mbps X-band link, derives reaction-wheel torque and momentum requirements,
estimates propulsion propellant and radiator area, and produces a provisional
mass allocation against the 60 kg wet-mass limit. Outputs are written to
`results/spacecraft_subsystems/`.

## Phase 7 integrated baseline

The integration model imports results from all earlier phases, assigns selected
system capacities and calculates margins for mass, power, storage, downlink,
ADCS, propulsion, thermal control and communications. It also creates a formal
requirements-verification matrix with Pass, Fail and Open states. Outputs are
written to `results/integrated_budgets/`.

## Phase 8 spacecraft configuration

The configuration model defines the spacecraft bus, component bounding boxes,
mass locations, centre of mass, deployed solar arrays, radiator allocation and
payload accommodation. It generates 3D and orthographic drawings, a component
layout CSV, a CAD dimension sheet and an ASCII STL concept model in
`results/spacecraft_configuration/`.

## Phase 9 robustness

The reproducible Monte Carlo model varies payload signal, mass growth, solar
degradation, communications losses, spacecraft inertia, disturbance torque,
delta-v demand, thermal load, data volume and ground availability. It reports
constraint pass rates, overall budget closure, a hardened design comparison
and global sensitivity correlations in `results/monte_carlo_robustness/`.

## Phase 10 final design review

The final review strengthens the allocations exposed by Phase 9 and evaluates a
four-site polar ground network. The selected concept achieves 98.48% simultaneous
budget closure in the reproducible 5,000-case study and a modeled 1.39 h worst
priority latency. Fifteen concept-level requirements pass and the three-year
mission-life verification remains explicitly open. The final report and review
evidence are written to `results/final_design_review/`.

## Engineering scope

This repository is a preliminary systems-design portfolio study. Results use
transparent engineering assumptions and simplified analytical models. They do
not represent flight qualification, detailed optical design, licensed ground
service, component procurement or validated mission performance.
