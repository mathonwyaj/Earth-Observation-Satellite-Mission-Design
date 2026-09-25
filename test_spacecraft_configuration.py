import tempfile
import unittest
from pathlib import Path
import numpy as np
from spacecraft_configuration import COMPONENTS, SELECTED_RADIATOR_AREA_M2, SELECTED_SOLAR_AREA_M2, centre_of_mass_m, component_inside_bus, deployed_envelope_m, total_mass_kg, write_stl
from spacecraft_subsystems import evaluate_subsystems


class SpacecraftConfigurationTests(unittest.TestCase):
    def test_configured_mass_matches_phase6(self):
        self.assertAlmostEqual(total_mass_kg(), evaluate_subsystems().wet_mass_with_system_margin_kg, places=3)

    def test_components_fit_bus_envelope(self):
        self.assertTrue(all(component_inside_bus(c) for c in COMPONENTS))

    def test_centre_of_mass_is_near_bus_centre(self):
        self.assertLess(np.linalg.norm(centre_of_mass_m()), 0.03)

    def test_solar_area_exceeds_requirement(self):
        self.assertGreaterEqual(SELECTED_SOLAR_AREA_M2, evaluate_subsystems().required_solar_array_area_m2)

    def test_radiator_area_exceeds_requirement(self):
        self.assertGreaterEqual(SELECTED_RADIATOR_AREA_M2, evaluate_subsystems().radiator_area_m2)

    def test_deployed_width_exceeds_stowed_width(self):
        self.assertGreater(deployed_envelope_m()[0], 0.70)

    def test_stl_is_generated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "concept.stl"; write_stl(path)
            text = path.read_text(encoding="ascii")
            self.assertTrue(text.startswith("solid")); self.assertGreater(text.count("facet normal"), 100)


if __name__ == "__main__": unittest.main()
