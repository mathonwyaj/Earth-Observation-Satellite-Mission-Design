import math
import unittest

import numpy as np

from orbit_coverage import (
    OrbitCase,
    access_event_times,
    coverage_half_angle_rad,
    evaluate_case,
    orbital_period_min,
    propagate_ground_track,
    sun_synchronous_inclination_deg,
)


class OrbitCoverageTests(unittest.TestCase):
    def test_sso_inclination_is_retrograde(self):
        inclination = sun_synchronous_inclination_deg(550.0)
        self.assertGreater(inclination, 97.0)
        self.assertLess(inclination, 99.0)

    def test_period_is_plausible(self):
        period = orbital_period_min(550.0)
        self.assertGreater(period, 94.0)
        self.assertLess(period, 97.0)

    def test_off_nadir_increases_coverage(self):
        nadir = coverage_half_angle_rad(550.0, 81.92, 0.0)
        agile = coverage_half_angle_rad(550.0, 81.92, 25.0)
        self.assertGreater(agile, nadir)

    def test_ground_track_coordinates_are_bounded(self):
        _, lat, lon = propagate_ground_track(550.0, 0.1, 30.0)
        self.assertTrue(np.all(np.abs(lat) <= 90.0))
        self.assertTrue(np.all(np.abs(lon) <= 180.0))

    def test_access_samples_are_collapsed_into_events(self):
        times = np.arange(0.0, 80.0, 10.0)
        access = np.array([False, True, True, False, False, True, True, False])
        events = access_event_times(times, access)
        self.assertEqual(len(events), 2)

    def test_case_returns_all_five_sites(self):
        result = evaluate_case(OrbitCase(550.0, 25.0), duration_days=20.0)
        self.assertEqual(result.sites_with_two_or_more_accesses, 5)
        self.assertTrue(math.isfinite(result.worst_site_max_revisit_h))

    def test_two_spacecraft_improve_revisit(self):
        single = evaluate_case(OrbitCase(550.0, 25.0, constellation_size=1))
        pair = evaluate_case(OrbitCase(550.0, 25.0, constellation_size=2))
        self.assertLess(pair.worst_site_max_revisit_h, single.worst_site_max_revisit_h)


if __name__ == "__main__":
    unittest.main()
