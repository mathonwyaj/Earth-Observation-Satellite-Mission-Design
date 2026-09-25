# Phase 4 Orbit and UK Coverage Trade

This phase compares circular sun-synchronous orbit candidates from 450 to
650 km. Inclination is calculated from the secular J2 nodal-precession
condition. Earth-fixed ground tracks include Earth rotation and the matching
sun-synchronous RAAN drift.

Preliminary revisit is evaluated at London, Cardiff, Manchester, Edinburgh and
Belfast over 20 days. Nadir-only access is compared with 15 and 25 degree
off-nadir agility. One- and two-spacecraft, evenly phased same-plane
architectures are compared. The payload field of view is included when
calculating each coverage footprint.

This is a representative-site engineering trade rather than complete national
coverage verification. A later refinement may use a UK land polygon, terrain,
cloud climatology and constrained observation scheduling.

The preferred solution is selected by minimum spacecraft count, then by
consistency with the established 550 km payload baseline, then by minimum
off-nadir agility. Off-nadir products will have degraded projected GSD relative
to the stated 10 m nadir GSD and must be characterised in a later refinement.

Run `python orbit_coverage.py` to generate the orbit trade CSV, revisit plot and
preferred-orbit ground track.
