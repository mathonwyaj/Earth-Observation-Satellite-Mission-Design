import unittest
import numpy as np
from monte_carlo_robustness import SEED, generate_uncertainties, run_monte_carlo


class MonteCarloRobustnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mc_results = run_monte_carlo(cases=1000, seed=SEED)

    def test_reproducible_seed(self):
        first = generate_uncertainties(10, SEED)["mass_growth_factor"]
        second = generate_uncertainties(10, SEED)["mass_growth_factor"]
        np.testing.assert_allclose(first, second)

    def test_all_arrays_have_requested_length(self):
        uncertainties, results, _, _, _, _ = self.mc_results
        self.assertTrue(all(len(values) == 1000 for values in uncertainties.values()))
        self.assertTrue(all(len(values) == 1000 for values in results.values()))

    def test_pass_rates_are_probabilities(self):
        rates = self.mc_results[3]
        self.assertTrue(all(0.0 <= value <= 100.0 for value in rates.values()))

    def test_known_latency_gap_prevents_full_success(self):
        self.assertEqual(self.mc_results[5].full_mission_success_percent, 0.0)

    def test_hardening_improves_budget_closure(self):
        summary = self.mc_results[5]
        self.assertGreater(summary.hardened_budget_success_percent, summary.baseline_budget_success_percent)

    def test_daily_data_balance_is_robust(self):
        self.assertGreater(self.mc_results[3]["Daily data balance"], 99.0)

    def test_sensitivity_correlations_are_bounded(self):
        self.assertTrue(all(-1.0 <= value <= 1.0 for value in self.mc_results[4].values()))


if __name__ == "__main__": unittest.main()
