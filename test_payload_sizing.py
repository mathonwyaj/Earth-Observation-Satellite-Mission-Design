import math
import unittest

from payload_sizing import PayloadDesign, size_payload


class PayloadSizingTests(unittest.TestCase):
    def setUp(self):
        self.result = size_payload(
            PayloadDesign(
                altitude_km=550,
                pixel_pitch_um=10,
                cross_track_pixels=8192,
                target_gsd_m=10,
            )
        )

    def test_focal_length(self):
        self.assertTrue(math.isclose(self.result.focal_length_mm, 550.0))

    def test_swath_width(self):
        self.assertTrue(math.isclose(self.result.swath_width_km, 81.92))

    def test_requirement(self):
        self.assertTrue(self.result.meets_50_km_swath)

    def test_positive_physical_outputs(self):
        self.assertGreater(self.result.diffraction_aperture_mm, 0)
        self.assertGreater(self.result.maximum_exposure_ms, 0)
        self.assertGreater(self.result.orbital_speed_km_s, 0)


if __name__ == "__main__":
    unittest.main()

