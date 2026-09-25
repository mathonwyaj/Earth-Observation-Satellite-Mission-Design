import unittest
from spacecraft_subsystems import SubsystemInputs, evaluate_subsystems, power_sizing, propulsion_sizing, thermal_sizing, xband_link_budget


class SpacecraftSubsystemTests(unittest.TestCase):
    def setUp(self): self.inputs = SubsystemInputs(); self.result = evaluate_subsystems(self.inputs)

    def test_power_system_closes(self):
        average, array_power, area, battery = power_sizing(self.inputs)
        self.assertGreater(array_power, average); self.assertGreater(area, 0.0); self.assertGreater(battery, 0.0)

    def test_array_area_responds_to_degradation(self):
        new = power_sizing(SubsystemInputs(mission_life_years=1.0))[2]
        old = power_sizing(SubsystemInputs(mission_life_years=5.0))[2]
        self.assertGreater(old, new)

    def test_xband_link_has_positive_margin(self):
        ebn0, margin = xband_link_budget(self.inputs)
        self.assertGreater(ebn0, 8.0); self.assertGreater(margin, 0.0)

    def test_selected_wheel_exceeds_minimums(self):
        self.assertGreaterEqual(self.result.selected_wheel_torque_nm, self.result.minimum_control_torque_nm)
        self.assertGreaterEqual(self.result.selected_wheel_momentum_nms, self.result.minimum_momentum_capacity_nms)

    def test_propellant_increases_with_delta_v(self):
        baseline = propulsion_sizing(self.inputs)[1]
        higher = propulsion_sizing(SubsystemInputs(delta_v_base_m_s=80.0))[1]
        self.assertGreater(higher, baseline)

    def test_radiator_area_is_physical(self):
        area = thermal_sizing(self.inputs)
        self.assertGreater(area, 0.0); self.assertLess(area, 2.0)

    def test_preliminary_mass_is_below_limit(self):
        self.assertGreater(self.result.wet_mass_margin_kg, 0.0)
        self.assertLess(self.result.wet_mass_with_system_margin_kg, self.inputs.wet_mass_limit_kg)


if __name__ == "__main__": unittest.main()
