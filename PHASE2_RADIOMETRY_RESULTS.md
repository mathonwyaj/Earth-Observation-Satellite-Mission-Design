# Phase 2 Radiometry and Data-Budget Trade

The 550 km, 10 m GSD, 81.92 km swath baseline has been extended to a
four-band multispectral concept: blue, green, red and near-infrared. Green and
NIR permit a normalized-difference water index, while visible bands support
contextual mapping and false-colour products.

The calculation is deliberately first order. It converts assumed Lambertian
target radiance into collected photons and detector electrons, then combines
photon shot noise, read noise and dark current. All environmental and detector
values remain visible in `payload_radiometry.py`.

## Baseline assumptions

- 80 mm clear aperture
- 0.60 ms exposure
- 35 percent optical throughput
- 60 percent quantum efficiency
- 12 electron read noise
- 12-bit samples and 4:1 compression
- 1,000 km reference imaging strip

## Interpretation

The dark-water reflectance case is intentionally demanding, particularly in
NIR where water is weakly reflective. The aperture trade therefore exposes the
performance sensitivity instead of assuming a payload already meets an SNR
requirement. The next design decision should balance SNR against telescope
diameter, mass, packaging and pointing stability.

Data-rate results size onboard storage and the communications subsystem. They
are instantaneous pushbroom imaging rates; mission-average downlink demand will
depend on the imaging schedule, cloud screening, compression and ground-station
contact plan developed in later phases.
