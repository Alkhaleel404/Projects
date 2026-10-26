import unittest
from datetime import datetime, timezone
from urllib.error import HTTPError
from unittest.mock import patch

from flood_data import (
    DataSourceError,
    _validate_external_url,
    _request_json,
    fetch_fema_hazards,
    fetch_floodnet_events,
    normalize_fema_geojson,
    normalize_floodnet_records,
    normalize_nws_alerts,
    normalize_nws_forecast,
)


class FloodDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 10, 25, 12, tzinfo=timezone.utc)

    def test_fema_geojson_is_normalized_with_wgs84_coordinates(self) -> None:
        payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [-73.8, 40.7],
                                [-73.7, 40.7],
                                [-73.7, 40.8],
                                [-73.8, 40.7],
                            ]
                        ],
                    },
                    "properties": {"FLD_ZONE": "AE", "ZONE_SUBTY": "1% annual chance"},
                }
            ],
        }

        result = normalize_fema_geojson(payload, retrieved_at=self.now)
        self.assertEqual(result["feature_count"], 1)
        self.assertEqual(result["skipped_feature_count"], 0)
        self.assertEqual(result["features"][0]["geometry"]["coordinates"][0][0][0], -73.8)
        self.assertEqual(result["retrieved_at"], self.now.isoformat())

    def test_fema_malformed_or_missing_data_is_not_success_shaped(self) -> None:
        with self.assertRaises(DataSourceError):
            normalize_fema_geojson([])
        with self.assertRaises(DataSourceError):
            normalize_fema_geojson({"type": "FeatureCollection"})
        with self.assertRaises(DataSourceError):
            normalize_fema_geojson(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [[[181, 40], [181, 40], [181, 40]]],
                            },
                            "properties": {},
                        }
                    ],
                }
            )

    def test_fema_reports_unusable_features_when_usable_features_remain(self) -> None:
        result = normalize_fema_geojson(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [[-73.8, 40.7], [-73.7, 40.7], [-73.7, 40.8], [-73.8, 40.7]]
                            ],
                        },
                        "properties": {"FLD_ZONE": "AE"},
                    },
                    {"type": "Feature", "geometry": None, "properties": {}},
                ],
            },
            retrieved_at=self.now,
        )
        self.assertEqual(result["feature_count"], 1)
        self.assertEqual(result["skipped_feature_count"], 1)

    def test_nws_forecast_requires_periods_and_normalizes_precipitation(self) -> None:
        result = normalize_nws_forecast(
            {
                "properties": {
                    "updateTime": "2026-10-25T15:00:00+00:00",
                    "generatedAt": "2026-10-25T15:05:00+00:00",
                    "periods": [
                        None,
                        {
                            "name": "Tonight",
                            "shortForecast": "Rain likely",
                            "startTime": "2026-10-25T18:00:00-04:00",
                            "temperature": 55,
                            "temperatureUnit": "F",
                            "probabilityOfPrecipitation": {"value": 70},
                        }
                    ],
                }
            }
        )
        self.assertEqual(result["periods"][0]["precipitation_probability"], 70)
        self.assertEqual(result["skipped_period_count"], 1)
        self.assertEqual(result["updated"], "2026-10-25T15:00:00+00:00")
        self.assertEqual(result["generated_at"], "2026-10-25T15:05:00+00:00")
        with self.assertRaises(DataSourceError):
            normalize_nws_forecast({"properties": {"periods": []}})

    def test_empty_nws_alert_collection_is_valid(self) -> None:
        result = normalize_nws_alerts(
            {"type": "FeatureCollection", "features": [], "updated": "2026-10-25T12:00:00Z"}
        )
        self.assertEqual(result["alerts"], [])
        self.assertEqual(result["skipped_alert_count"], 0)
        with self.assertRaises(DataSourceError):
            normalize_nws_alerts({"type": "FeatureCollection", "features": None})
        with self.assertRaises(DataSourceError):
            normalize_nws_alerts([])

    def test_nws_alerts_report_malformed_entries(self) -> None:
        result = normalize_nws_alerts(
            {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "properties": {"event": "Flood Warning"}},
                    {"type": "Feature", "properties": None},
                ],
            }
        )
        self.assertEqual(len(result["alerts"]), 1)
        self.assertEqual(result["skipped_alert_count"], 1)

    def test_floodnet_joins_sensor_ids_and_keeps_latest_historical_event(self) -> None:
        result = normalize_floodnet_records(
            [
                {
                    "sensor_id": "Q-sensor-1",
                    "sensor_name": "Sensor 1",
                    "flood_start_time": "2026-10-01T10:00:00.000",
                    "max_depth_inches": "2.0",
                    "duration_mins": "12",
                },
                {
                    "sensor_id": "Q-sensor-1",
                    "sensor_name": "Sensor 1",
                    "flood_start_time": "2026-10-02T10:00:00.000",
                    "max_depth_inches": "3.5",
                    "duration_mins": "30",
                },
            ],
            [
                {
                    "sensor_id": "Q-sensor-1",
                    "sensor_name": "Sensor 1",
                    "borough": "Queens",
                    "longitude": "-73.8",
                    "latitude": "40.7",
                }
            ],
            retrieved_at=self.now,
        )

        self.assertEqual(result["feature_count"], 1)
        feature = result["features"][0]
        self.assertEqual(feature["geometry"]["coordinates"], [-73.8, 40.7])
        self.assertEqual(feature["properties"]["max_depth_inches"], 3.5)
        self.assertFalse(result["dataset_timestamp_has_timezone"])

    def test_floodnet_malformed_values_are_skipped(self) -> None:
        result = normalize_floodnet_records(
            [
                {
                    "sensor_id": "Q-sensor-1",
                    "flood_start_time": "not-a-time",
                    "max_depth_inches": "2000",
                    "duration_mins": "1",
                }
            ],
            [
                {
                    "sensor_id": "Q-sensor-1",
                    "borough": "Queens",
                    "longitude": "0",
                    "latitude": "0",
                }
            ],
            retrieved_at=self.now,
        )
        self.assertEqual(result["features"], [])
        self.assertEqual(result["skipped_event_count"], 1)

    def test_network_and_malformed_service_failures_are_explicit(self) -> None:
        with patch("flood_data._request_json", side_effect=DataSourceError("offline")):
            with self.assertRaisesRegex(DataSourceError, "offline"):
                fetch_fema_hazards()
        with patch("flood_data._request_json", return_value={"type": "FeatureCollection"}):
            with self.assertRaises(DataSourceError):
                fetch_fema_hazards()
        with patch("flood_data._request_json", side_effect=[[], []]):
            self.assertEqual(fetch_floodnet_events()["features"], [])

    def test_outbound_hosts_are_restricted_to_verified_https_sources(self) -> None:
        _validate_external_url("https://api.weather.gov/points/40.7,-73.8")
        with self.assertRaises(DataSourceError):
            _validate_external_url("http://api.weather.gov/points/")
        with self.assertRaises(DataSourceError):
            _validate_external_url("https://example.com/")
        with self.assertRaises(DataSourceError):
            _validate_external_url("https://api.weather.gov:8443/points/")

    def test_timeout_malformed_json_and_rate_limit_errors_are_explicit(self) -> None:
        with patch("flood_data.build_opener") as build_opener:
            build_opener.return_value.open.side_effect = TimeoutError("slow")
            with self.assertRaisesRegex(DataSourceError, "could not be reached"):
                _request_json("https://api.weather.gov/points/40.7,-73.8")

        with patch("flood_data.build_opener") as build_opener:
            response = build_opener.return_value.open.return_value.__enter__.return_value
            response.read.return_value = b"not valid JSON"
            with self.assertRaisesRegex(DataSourceError, "malformed JSON"):
                _request_json("https://api.weather.gov/points/40.7,-73.8")

        with patch("flood_data.build_opener") as build_opener:
            build_opener.return_value.open.side_effect = HTTPError(
                "https://api.weather.gov/points/40.7,-73.8",
                429,
                "rate limited",
                {},
                None,
            )
            with self.assertRaisesRegex(DataSourceError, "HTTP 429"):
                _request_json("https://api.weather.gov/points/40.7,-73.8")


if __name__ == "__main__":
    unittest.main()
