import math
import unittest
import numpy as np
from mission_operations import OperationsInputs, contact_windows, run_trade, station_central_angle_limit_rad


class MissionOperationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = {result.network: result for result in run_trade()}

    def test_station_visibility_angle_is_physical(self):
        limit = station_central_angle_limit_rad(550.0, 10.0)
        self.assertGreater(limit, 0.0); self.assertLess(limit, math.acos(6_371_000.0 / 6_921_000.0))

    def test_contact_windows_are_collapsed(self):
        times = np.arange(0.0, 70.0, 10.0); visible = np.array([False, True, True, False, True, True, False])
        self.assertEqual(contact_windows(times, visible), [(10.0, 30.0), (40.0, 60.0)])

    def test_two_station_network_increases_capacity(self):
        self.assertGreater(self.results["Goonhilly + Svalbard"].daily_downlink_capacity_gbit_per_spacecraft, self.results["Goonhilly only"].daily_downlink_capacity_gbit_per_spacecraft)

    def test_preferred_network_closes_daily_data_budget(self):
        preferred = self.results["Goonhilly + Svalbard"]
        self.assertTrue(preferred.meets_daily_capacity); self.assertGreater(preferred.capacity_margin_percent, 0.0)

    def test_preferred_network_has_finite_storage_requirement(self):
        storage = self.results["Goonhilly + Svalbard"].recommended_storage_gb_per_spacecraft
        self.assertGreater(storage, 0.0); self.assertLess(storage, 256.0)

    def test_three_hour_gap_is_reported_not_hidden(self):
        preferred = self.results["Goonhilly + Svalbard"]
        self.assertFalse(preferred.meets_three_hour_priority_target)
        self.assertGreater(preferred.worst_priority_latency_h, 3.0)

    def test_scene_rate_increase_raises_generated_data(self):
        four = run_trade(OperationsInputs(scenes_per_day_per_spacecraft=4))[1]
        eight = run_trade(OperationsInputs(scenes_per_day_per_spacecraft=8))[1]
        self.assertGreater(eight.daily_generated_data_gbit_per_spacecraft, four.daily_generated_data_gbit_per_spacecraft)


if __name__ == "__main__": unittest.main()
