# Phase 8 — Spacecraft Configuration and Preliminary CAD

This phase converts the integrated budgets into a physical configuration for
one spacecraft. The model defines the bus and deployed envelopes, component
bounding boxes, mass locations, centre of mass, solar wings, radiator area and
payload placement.

The generated STL is a concept envelope for visualisation and CAD import. It is
not a manufacturing model, detailed mechanical assembly or structurally
verified design. The component bounding boxes and dimension sheet are intended
to guide a later parametric SolidWorks assembly.

Run `python spacecraft_configuration.py` to regenerate all drawings and CAD
outputs. Run `python -m unittest discover -v` to verify every project phase.
