import unittest

from coverage_analysis import haversine_m, normalize_sensor_locations, sample_monitoring_gaps


class CoverageAnalysisTests(unittest.TestCase):
    def test_haversine_same_point_is_zero(self):
        self.assertAlmostEqual(haversine_m((40.7, -73.8), (40.7, -73.8)), 0)

    def test_haversine_known_short_distance_is_reasonable(self):
        distance = haversine_m((40.7, -73.8), (40.71, -73.8))
        self.assertGreater(distance, 1000)
        self.assertLess(distance, 1200)

    def test_normalize_filters_invalid_and_non_queens_rows(self):
        rows = [
            {"sensor_id": "Q-1", "sensor_name": "One", "latitude": "40.7", "longitude": "-73.8", "borough": "Queens"},
            {"sensor_id": "Q-1", "sensor_name": "Duplicate", "latitude": "40.7", "longitude": "-73.8", "borough": "Queens"},
            {"sensor_id": "B-1", "latitude": "40.7", "longitude": "-73.8", "borough": "Brooklyn"},
            {"sensor_id": "Q-bad", "latitude": "999", "longitude": "0", "borough": "Queens"},
        ]
        result = normalize_sensor_locations(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sensor_id"], "Q-1")

    def test_grid_reports_gap_distances_and_is_bounded(self):
        sensors = normalize_sensor_locations([
            {"sensor_id": "Q-1", "sensor_name": "West", "latitude": "40.7", "longitude": "-73.8", "borough": "Queens"},
            {"sensor_id": "Q-2", "sensor_name": "East", "latitude": "40.7", "longitude": "-73.75", "borough": "Queens"},
        ])
        result = sample_monitoring_gaps(sensors)
        self.assertEqual(result["sensor_count"], 2)
        self.assertGreater(result["sample_count"], 0)
        self.assertLessEqual(result["sample_count"], 3600)
        self.assertGreater(result["over_2km_count"], 0)
        self.assertTrue(all(point["distance_m"] >= 0 for point in result["points"]))

    def test_grid_rejects_empty_sensor_inventory(self):
        with self.assertRaises(ValueError):
            sample_monitoring_gaps([])


if __name__ == "__main__":
    unittest.main()
