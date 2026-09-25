# Phase 3 Payload Optimisation

The Phase 2 optical model has been converted into a constrained design search.
The optimiser varies clear aperture and exposure time and compares standard and
enhanced detector scenarios. It enforces the 10 m GSD configuration, the
0.5-pixel smear limit, diffraction sizing and a provisional worst-band SNR of
at least 50.

The preferred baseline is selected only from the conservative standard
detector assumptions: 35 percent optical throughput and 60 percent quantum
efficiency. The enhanced case is a sensitivity study, not a claimed component.

Payload mass and telescope envelope are parametric estimates for early trades.
They must be replaced by CAD-derived mass properties and mechanical packaging
in the later spacecraft configuration phase.

Run `python payload_optimisation.py` to regenerate the CSV and figures. The
console output records the selected aperture, exposure, limiting spectral band,
SNR values, f-number, smear and preliminary resource estimates.
