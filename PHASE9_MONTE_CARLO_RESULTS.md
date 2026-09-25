# Phase 9 — Monte Carlo Robustness and Sensitivity

This phase propagates uncertainty through payload SNR, spacecraft mass, power,
communications, ADCS, propulsion, thermal control, data volume and ground
operations. The deterministic seed makes the 5,000-case baseline reproducible.

The response surfaces are anchored to the deterministic design but are still
concept-level approximations. They reveal margin sensitivity; they do not
replace detailed subsystem models, supplier data or qualification testing.

Two closure rates are reported: the current baseline and a proposed hardened
scenario. Full mission success also includes the known three-hour latency
requirement and therefore remains zero until the ground architecture changes.

## Reproducible 5,000-case result

| Result | Value |
|---|---:|
| Baseline simultaneous budget closure | 10.02% |
| Hardened simultaneous budget closure | 92.66% |
| Full mission success including three-hour delivery | 0.00% |
| Dominant individual baseline failure | Payload SNR |
| Strongest minimum-margin sensitivity | Disturbance torque |

The weakest individual pass rates are payload SNR (57.98%), wheel torque
(60.74%), delta-v (64.26%), wheel momentum (67.92%) and X-band margin
(74.20%). Daily data balance and the 8 GB baseline storage allocation pass all
sampled cases. The 10.02% system value is lower than every individual rate
because every modeled constraint must pass simultaneously.

The hardened comparison uses a 180 mm aperture proxy, 180 W end-of-life array
capacity, 3 dB additional communications margin, 0.015 N m / 0.15 N m s wheel
capability, 60 m/s delta-v, 0.70 m² radiator area and 16 GB storage. These are
candidate allocations for the next design iteration, not selected flight
hardware. Reaching a 95% robustness target will require another targeted trade,
and the three-hour delivery requirement needs a change to the ground or relay
architecture rather than additional spacecraft budget margin.

Run `python monte_carlo_robustness.py` to regenerate the case data, risk summary
and figures. Run `python -m unittest discover -v` to verify every project phase.
