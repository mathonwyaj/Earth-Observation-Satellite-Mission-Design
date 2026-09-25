# Phase 7 — Integrated Budgets and Requirements Verification

This phase creates the first consistent system-level baseline by importing the
payload, orbit, operations and spacecraft-subsystem results. It records selected
capacities, calculated needs, design margins and verification status.

The requirements matrix deliberately retains failures and open items. Passing a
software test means the calculation behaves as intended; it does not turn an
unmet engineering requirement into a pass.

## Baseline status

- Requirements passed: 13
- Requirements failed: 1
- Requirements open: 1
- Total requirements tracked: 15
- Smallest positive integrated budget margin: 3.13%

`MIS-004`, priority product delivery within three hours, remains failed because
the preferred two-station network gives a preliminary worst-case latency of
approximately 7.00 hours. `MIS-005`, three-year mission life, remains open until
reliability, radiation, component derating and lifetime analyses are performed.

The narrowest positive budget is reaction-wheel torque: 0.010 N m selected
against 0.00970 N m calculated. This selection requires additional margin or a
higher-torque wheel before the design is frozen.

Run `python integrated_budgets.py` to regenerate the CSV, JSON and figure.
Run `python -m unittest discover -v` to verify every project phase.
