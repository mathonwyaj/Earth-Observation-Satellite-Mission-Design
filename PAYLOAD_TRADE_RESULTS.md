# Preliminary Payload Trade Results

## Status

Phase 1 preliminary result. These calculations size an ideal nadir-looking optical system. They do not yet include detector MTF, optical transmission, signal-to-noise ratio, Earth curvature, off-nadir viewing, atmospheric effects, cloud availability, or detailed time-delay-integration behaviour.

## Baseline case evaluated

| Parameter | Preliminary value |
|---|---:|
| Orbit altitude | 550 km |
| Target ground-sampling distance | 10 m |
| Pixel pitch | 10 micrometres |
| Cross-track pixels | 8192 |
| Longest sizing wavelength | 850 nm |
| Smear allowance | 0.5 pixel |

## First-order results

| Output | Result |
|---|---:|
| Required focal length | 550.0 mm |
| Detector width | 81.92 mm |
| Cross-track field of view | 8.52 deg |
| Nadir swath width | 81.92 km |
| Rayleigh-limit aperture estimate at 850 nm | 57.04 mm |
| Corresponding f-number | f/9.64 |
| Circular-orbit speed estimate | 7.585 km/s |
| Maximum exposure for 0.5-pixel smear | 0.659 ms |

## Detector-width decision

At 10 m GSD, the first-order nadir swath is the cross-track pixel count multiplied by the GSD:

- 4096 pixels: 40.96 km - fails the 50 km preliminary requirement.
- 6144 pixels: 61.44 km - passes with limited margin.
- 8192 pixels: 81.92 km - passes with greater coverage margin.

The 8192-pixel option remains the working baseline because it provides useful swath margin. It is not selected finally until detector availability, optical packaging, SNR, data rate, power, cost, and pointing/image-smear performance are assessed.

## Altitude trade observation

For fixed GSD and pixel pitch, required focal length grows linearly with altitude. With 10 micrometre pixels and a 10 m GSD target:

- 450 km altitude requires approximately 450 mm focal length.
- 550 km altitude requires approximately 550 mm focal length.
- 650 km altitude requires approximately 650 mm focal length.

The orbit decision must therefore trade coverage, lifetime, drag, revisit performance, radiation exposure, aperture, focal length, and spacecraft packaging.

## Preliminary conclusion

A 10 m-class, greater-than-50 km-swath multispectral concept is geometrically credible at 550 km using a detector with at least 6144 cross-track pixels. The 8192-pixel working baseline produces an 81.92 km ideal swath but requires a relatively long 550 mm focal length for 10 micrometre pixels. Smaller pixels may materially reduce payload length and will be evaluated alongside diffraction, SNR, and commercially credible detector formats.

## Next analysis

1. Add spectral bands appropriate for water discrimination.
2. Add diffraction MTF and detector-sampling criteria.
3. Estimate photon signal, noise, and required aperture/exposure.
4. Evaluate smaller pixel pitches and folded optical layouts.
5. Calculate raw and compressed payload data rates.
6. Feed viable payload cases into the orbit and revisit model.

