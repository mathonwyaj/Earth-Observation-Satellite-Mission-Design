# Phase 5 — Mission Operations, Storage and Downlink

This phase connects the compressed image volume from Phase 2 to a preliminary
operations concept for the two-spacecraft mission selected in Phase 4.

The model includes geometric access to Goonhilly and Svalbard, a 10-degree
minimum elevation mask, four 1,000 km scenes per spacecraft per day, a 150 Mbps
X-band downlink, 70% link/protocol efficiency, 90% station availability and a
20% storage margin.

The station coordinates and availability are preliminary design assumptions.
This is not a detailed RF link budget, licensed ground-service commitment or
operational pass schedule.

## Baseline numerical results

Each spacecraft generates 39.322 Gbit/day from four representative scenes.

| Network | Passes/day/spacecraft | Usable capacity | Recommended storage | Worst priority latency | Daily balance | 3 h target |
|---|---:|---:|---:|---:|---|---|
| Goonhilly only | 4.14 | 143.37 Gbit/day | 2.95 GB | 9.94 h | Pass | Fail |
| Goonhilly + Svalbard | 13.57 | 562.28 Gbit/day | 2.95 GB | 7.00 h | Pass | Fail |

The two-station network provides a very large average capacity margin, but the
timing of acquisitions relative to passes still creates a worst-case latency
above three hours. Phase 5 therefore does **not** claim that the priority
delivery requirement is closed. A broader ground network, inter-satellite or
relay communications, acquisition scheduling, or a revised requirement must
be traded later.

The current capacity calculation treats each spacecraft independently and does
not yet resolve simultaneous demands on a shared antenna. Storage is a minimum
preliminary result from the seven-day deterministic scenario, not a final
hardware capacity selection.

Run `python mission_operations.py` to regenerate the numerical summary, CSV and
plots. Run `python -m unittest discover -v` to verify all project phases.
