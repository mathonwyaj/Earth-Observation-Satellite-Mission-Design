import unittest

from final_design_review import (
    SelectedDesign,
    build_requirements,
    evaluate_final_network,
    final_robustness,
    review_summary,
)


class FinalDesignReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = SelectedDesign()
        cls.closure, cls.rates = final_robustness(cases=1000)
        cls.requirements = build_requirements(cls.design)

    def test_final_robustness_exceeds_target(self):
        self.assertGreaterEqual(self.closure, 95.0)

    def test_every_individual_budget_exceeds_target(self):
        self.assertTrue(all(rate >= 95.0 for rate in self.rates.values()))

    def test_four_site_network_meets_latency(self):
        self.assertLessEqual(evaluate_final_network().worst_priority_latency_h, 3.0)

    def test_requirement_identifiers_are_unique(self):
        identifiers = [item.identifier for item in self.requirements]
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_no_failed_requirements_remain(self):
        self.assertFalse(any(item.status == "Fail" for item in self.requirements))

    def test_lifetime_verification_remains_open(self):
        item = next(item for item in self.requirements if item.identifier == "MIS-005")
        self.assertEqual(item.status, "Open")

    def test_review_is_not_called_flight_qualified(self):
        summary = review_summary(self.requirements)
        self.assertIn("open verification", summary.review_outcome.lower())


if __name__ == "__main__": unittest.main()
