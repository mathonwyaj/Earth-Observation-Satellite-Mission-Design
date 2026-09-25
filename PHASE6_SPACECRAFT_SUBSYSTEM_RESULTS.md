# Phase 6 — Preliminary Spacecraft Subsystem Sizing

This phase sizes one spacecraft bus around the payload, orbit and operations
architecture selected in Phases 1–5. It covers electrical power, battery,
X-band communications, ADCS slew torque and momentum capacity, propulsion,
thermal rejection and a provisional subsystem mass allocation.

All inputs are explicit concept-design assumptions. The results are not vendor
selections, a detailed RF link budget, a qualification thermal model or a
critical design review budget.

## Baseline results per spacecraft

| Subsystem quantity | Preliminary result |
|---|---:|
| Average operational load | 62.46 W |
| Required end-of-life array power | 130.35 W |
| Solar-array area | 0.649 m² |
| Battery capacity | 53.47 Wh |
| X-band Eb/N0 | 11.86 dB |
| X-band link margin | 3.86 dB |
| Selected wheel torque | 0.010 N m |
| Selected wheel momentum | 0.100 N m s |
| Delta-v with margin | 48.0 m/s |
| Propellant | 1.32 kg |
| Radiator area | 0.534 m² |
| Wet mass including 15% dry-mass margin | 55.29 kg |
| Remaining mass margin to 60 kg | 4.71 kg |

The solar array is sized for orbit-average energy balance and eclipse recharge;
short imaging and downlink peaks require the battery and power electronics to
support peak load. The link result assumes a 2,000 km slant range and an
aggregate ground-station G/T; atmospheric, polarisation, pointing and hardware
losses require refinement. The thermal result is a single-node hot-case
radiator estimate. Phase 7 will integrate and trace the formal mass, power and
data budgets.

Run `python spacecraft_subsystems.py` to regenerate the results and figures.
Run `python -m unittest discover -v` to test every phase.
