import unittest

from payload_optimisation import (
    ENHANCED,
    STANDARD,
    evaluate_candidate,
    generate_trade,
    select_preferred,
)
from payload_sizing import PayloadDesign


class PayloadOptimisationTests(unittest.TestCase):
    def setUp(self):
        self.design = PayloadDesign(550.0, 10.0, 8192, 10.0)

    def test_aperture_improves_worst_band_snr(self):
        small = evaluate_candidate(self.design, STANDARD, 100.0, 0.60)
        large = evaluate_candidate(self.design, STANDARD, 170.0, 0.60)
        self.assertGreater(large.minimum_band_snr, small.minimum_band_snr)

    def test_exposure_above_smear_limit_is_rejected(self):
        result = evaluate_candidate(self.design, STANDARD, 200.0, 0.70)
        self.assertFalse(result.meets_smear)
        self.assertFalse(result.feasible)

    def test_enhanced_detector_improves_snr(self):
        standard = evaluate_candidate(self.design, STANDARD, 120.0, 0.60)
        enhanced = evaluate_candidate(self.design, ENHANCED, 120.0, 0.60)
        self.assertGreater(enhanced.minimum_band_snr, standard.minimum_band_snr)

    def test_preferred_design_meets_all_constraints(self):
        preferred = select_preferred(generate_trade(self.design))
        self.assertTrue(preferred.feasible)
        self.assertGreaterEqual(preferred.minimum_band_snr, 50.0)
        self.assertLessEqual(preferred.smear_pixels, 0.5)
        self.assertEqual(preferred.scenario, STANDARD.name)


if __name__ == "__main__":
    unittest.main()
