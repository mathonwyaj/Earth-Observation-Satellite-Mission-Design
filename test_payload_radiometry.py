import unittest

from payload_radiometry import (
    BANDS,
    RadiometryInputs,
    aperture_trade,
    band_radiometry,
    calculate_data_budget,
)
from payload_sizing import PayloadDesign


class PayloadRadiometryTests(unittest.TestCase):
    def setUp(self):
        self.design = PayloadDesign(550.0, 10.0, 8192, 10.0)
        self.inputs = RadiometryInputs()

    def test_all_band_results_are_physical(self):
        for band in BANDS:
            result = band_radiometry(band, self.design, self.inputs)
            self.assertGreater(result.signal_electrons, 0.0)
            self.assertGreater(result.snr, 0.0)

    def test_larger_aperture_improves_snr(self):
        trade = aperture_trade(self.design, self.inputs, [60.0, 80.0, 100.0])
        for values in trade.values():
            self.assertLess(values[0], values[1])
            self.assertLess(values[1], values[2])

    def test_compression_reduces_data_rate(self):
        budget = calculate_data_budget(self.design, self.inputs, len(BANDS))
        self.assertAlmostEqual(
            budget.raw_data_rate_mbps / budget.compressed_data_rate_mbps,
            self.inputs.compression_ratio,
        )

    def test_expected_line_rate(self):
        budget = calculate_data_budget(self.design, self.inputs, len(BANDS))
        self.assertGreater(budget.line_rate_hz, 700.0)
        self.assertLess(budget.line_rate_hz, 800.0)


if __name__ == "__main__":
    unittest.main()
