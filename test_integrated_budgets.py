import unittest
from integrated_budgets import integrated_budget_items, margin_above, margin_below, requirements_matrix


class IntegratedBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.budgets = integrated_budget_items(); cls.requirements = requirements_matrix()

    def test_margin_functions(self):
        self.assertAlmostEqual(margin_above(100.0, 120.0), 20.0)
        self.assertAlmostEqual(margin_below(60.0, 50.0), 20.0)

    def test_all_integrated_budgets_have_positive_margin(self):
        self.assertTrue(all(item.margin_percent > 0.0 for item in self.budgets))

    def test_requirement_identifiers_are_unique(self):
        identifiers = [r.identifier for r in self.requirements]
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_delivery_requirement_remains_failed(self):
        delivery = next(r for r in self.requirements if r.identifier == "MIS-004")
        self.assertEqual(delivery.status, "Fail")

    def test_mission_life_remains_open(self):
        life = next(r for r in self.requirements if r.identifier == "MIS-005")
        self.assertEqual(life.status, "Open")

    def test_mass_requirement_passes(self):
        mass = next(r for r in self.requirements if r.identifier == "SYS-001")
        self.assertEqual(mass.status, "Pass")

    def test_matrix_has_all_status_categories(self):
        self.assertEqual({r.status for r in self.requirements}, {"Pass", "Fail", "Open"})


if __name__ == "__main__": unittest.main()
