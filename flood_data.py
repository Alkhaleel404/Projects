"""Validated clients for the official FEMA and National Weather Service APIs."""

from __future__ import annotations

import json
import math
import re
import socket
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from http.client import HTTPException
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)


QUEENS_REFERENCE = (40.702, -73.8008)
FEMA_BOUNDS = (-73.83, 40.68, -73.78, 40.72)
FEMA_QUERY_URL = (
    "https://hazards.fema.gov/arcgis/rest/services/public/"
    "NFHL/MapServer/28/query"
)
NWS_POINTS_URL = "https://api.weather.gov/points/40.702,-73.8008"
MAX_RESPONSE_BYTES = 8_000_000
ALLOWED_HOSTS = frozenset(
    {"hazards.fema.gov", "api.weather.gov", "data.cityofnewyork.us"}
)
FLOODNET_EVENTS_URL = "https://data.cityofnewyork.us/resource/aq7i-eu5q.json"
FLOODNET_SENSORS_URL = "https://data.cityofnewyork.us/resource/kb2e-tjy3.json"


class DataSourceError(RuntimeError):
    """A public data source was unavailable or returned invalid data."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_external_url(url: str) -> None:
    parsed = urlparse(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise DataSourceError("The data source returned an unexpected service URL.") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
    ):
        raise DataSourceError("The data source returned an unexpected service URL.")


class _SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request: Request, response: Any, code: int, message: str, headers: Any, new_url: str) -> Request | None:
        _validate_external_url(new_url)
        return super().redirect_request(request, response, code, message, headers, new_url)


def _request_json(url: str, *, timeout: float = 12.0) -> Any:
    _validate_external_url(url)
    request = Request(
        url,
        headers={
            "Accept": "application/geo+json, application/json",
            "User-Agent": "RainRouteNYC/1.0 (public-data civic demonstration)",
        },
    )
    opener = build_opener(_SafeRedirectHandler())
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        raise DataSourceError(f"The data source returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, socket.timeout, HTTPException, OSError) as exc:
        raise DataSourceError("The public data source could not be reached.") from exc

    if len(body) > MAX_RESPONSE_BYTES:
        raise DataSourceError("The public data response exceeded the size limit.")
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError, RecursionError) as exc:
        raise DataSourceError("The public data source returned malformed JSON.") from exc
    return payload


def _valid_number(value: Any, *, minimum: float, maximum: float) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        numeric = float(value)
    except (OverflowError, ValueError):
        return False
    return math.isfinite(numeric) and minimum <= numeric <= maximum


def _valid_ring(ring: Any, point_count: list[int]) -> bool:
    if not isinstance(ring, list) or len(ring) < 4:
        return False
    if ring[0] != ring[-1]:
        return False
    for position in ring:
        if (
            not isinstance(position, list)
            or len(position) < 2
            or not _valid_number(position[0], minimum=-180, maximum=180)
            or not _valid_number(position[1], minimum=-90, maximum=90)
        ):
            return False
        point_count[0] += 1
        if point_count[0] > 50_000:
            return False
    return True


def _valid_polygon(coordinates: Any, point_count: list[int]) -> bool:
    return (
        isinstance(coordinates, list)
        and bool(coordinates)
        and all(_valid_ring(ring, point_count) for ring in coordinates)
    )


def _valid_geometry_coordinates(
    geometry_type: str,
    coordinates: Any,
    point_count: list[int],
) -> bool:
    if geometry_type == "Polygon":
        return _valid_polygon(coordinates, point_count)
    return (
        isinstance(coordinates, list)
        and bool(coordinates)
        and all(_valid_polygon(polygon, point_count) for polygon in coordinates)
    )


def normalize_fema_geojson(
    payload: dict[str, Any],
    *,
    retrieved_at: datetime | None = None,
) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise DataSourceError("FEMA returned an unexpected GeoJSON response.")
    features = payload.get("features")
    if not isinstance(features, list):
        raise DataSourceError("FEMA returned a malformed feature list.")

    normalized: list[dict[str, Any]] = []
    skipped_feature_count = 0
    point_count = [0]
    for feature in features[:500]:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            skipped_feature_count += 1
            continue
        geometry = feature.get("geometry")
        properties = feature.get("properties")
        if not isinstance(geometry, dict) or not isinstance(properties, dict):
            skipped_feature_count += 1
            continue
        geometry_type = geometry.get("type")
        coordinates = geometry.get("coordinates")
        if geometry_type not in ("Polygon", "MultiPolygon"):
            skipped_feature_count += 1
            continue
        if not _valid_geometry_coordinates(geometry_type, coordinates, point_count):
            skipped_feature_count += 1
            continue

        zone = properties.get("FLD_ZONE")
        subtype = properties.get("ZONE_SUBTY")
        normalized.append(
            {
                "type": "Feature",
                "geometry": {"type": geometry_type, "coordinates": coordinates},
                "properties": {
                    "FLD_ZONE": zone[:40] if isinstance(zone, str) else "Unknown",
                    "ZONE_SUBTY": subtype[:160] if isinstance(subtype, str) else "",
                },
            }
        )

    if features and not normalized:
        raise DataSourceError("FEMA returned no usable flood-zone geometries.")
    fetched_at = retrieved_at or _utc_now()
    if fetched_at.tzinfo is None:
        raise ValueError("The retrieval timestamp must include a timezone.")
    return {
        "type": "FeatureCollection",
        "features": normalized,
        "retrieved_at": fetched_at.astimezone(timezone.utc).isoformat(),
        "feature_count": len(normalized),
        "skipped_feature_count": skipped_feature_count,
        "possibly_truncated": len(features) >= 500,
        "data_timestamp": None,
    }


def fetch_fema_hazards() -> dict[str, Any]:
    west, south, east, north = FEMA_BOUNDS
    query = urlencode(
        {
            "where": "1=1",
            "geometry": f"{west},{south},{east},{north}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "outFields": "FLD_ZONE,ZONE_SUBTY",
            "returnGeometry": "true",
            "outSR": "4326",
            "resultRecordCount": "500",
            "f": "geojson",
        }
    )
    payload = _request_json(f"{FEMA_QUERY_URL}?{query}")
    return normalize_fema_geojson(payload)


def _fetch_nws_grid() -> tuple[str, str]:
    payload = _request_json(NWS_POINTS_URL)
    if not isinstance(payload, dict):
        raise DataSourceError("The NWS point service returned an invalid response.")
    properties = payload.get("properties")
    if not isinstance(properties, dict):
        raise DataSourceError("The NWS point service returned an invalid response.")

    forecast_url = properties.get("forecast")
    forecast_zone = properties.get("forecastZone")
    if not isinstance(forecast_url, str) or not isinstance(forecast_zone, str):
        raise DataSourceError("The NWS point service omitted forecast metadata.")
    _validate_external_url(forecast_url)
    if re.fullmatch(
        r"/gridpoints/[A-Z]{2,4}/\d+,\d+/forecast",
        urlparse(forecast_url).path,
    ) is None:
        raise DataSourceError("The NWS point service returned an invalid forecast URL.")
    zone_match = re.fullmatch(
        r"https://api\.weather\.gov/zones/forecast/(NYZ\d+)",
        forecast_zone,
    )
    if zone_match is None:
        raise DataSourceError("The NWS point service returned an invalid alert zone.")
    return forecast_url, zone_match.group(1)


def normalize_nws_forecast(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise DataSourceError("The NWS forecast response is malformed.")
    properties = payload.get("properties")
    if not isinstance(properties, dict) or not isinstance(properties.get("periods"), list):
        raise DataSourceError("The NWS forecast response is missing its forecast periods.")
    periods: list[dict[str, Any]] = []
    skipped_period_count = 0
    for period in properties["periods"][:8]:
        if not isinstance(period, dict):
            skipped_period_count += 1
            continue
        name = period.get("name")
        summary = period.get("shortForecast")
        start_time = period.get("startTime")
        if not all(isinstance(value, str) for value in (name, summary, start_time)):
            skipped_period_count += 1
            continue
        temperature = period.get("temperature")
        unit = period.get("temperatureUnit")
        probability = period.get("probabilityOfPrecipitation")
        precipitation = probability.get("value") if isinstance(probability, dict) else None
        if not _valid_number(precipitation, minimum=0, maximum=100):
            precipitation = None
        periods.append(
            {
                "name": name[:80],
                "short_forecast": summary[:200],
                "start_time": start_time,
                "temperature": (
                    temperature
                    if isinstance(temperature, int) and not isinstance(temperature, bool)
                    else None
                ),
                "temperature_unit": unit[:5] if isinstance(unit, str) else "",
                "precipitation_probability": precipitation,
            }
        )
    if not periods:
        raise DataSourceError("The NWS forecast response contained no usable periods.")
    updated = properties.get("updateTime") or properties.get("updated")
    generated_at = properties.get("generatedAt")
    return {
        "periods": periods,
        "skipped_period_count": skipped_period_count,
        "updated": updated if isinstance(updated, str) else None,
        "generated_at": generated_at if isinstance(generated_at, str) else None,
        "retrieved_at": _utc_now().isoformat(),
    }


def fetch_nws_forecast() -> dict[str, Any]:
    forecast_url, _ = _fetch_nws_grid()
    return normalize_nws_forecast(_request_json(forecast_url))


def normalize_nws_alerts(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise DataSourceError("The NWS alerts response is malformed.")
    features = payload.get("features")
    if payload.get("type") != "FeatureCollection" or not isinstance(features, list):
        raise DataSourceError("The NWS alerts response is malformed.")
    alerts: list[dict[str, Any]] = []
    skipped_alert_count = 0
    for feature in features[:50]:
        if not isinstance(feature, dict) or not isinstance(feature.get("properties"), dict):
            skipped_alert_count += 1
            continue
        properties = feature["properties"]
        event = properties.get("event")
        if not isinstance(event, str):
            skipped_alert_count += 1
            continue
        alerts.append(
            {
                "event": event[:120],
                "headline": (
                    properties["headline"][:240]
                    if isinstance(properties.get("headline"), str)
                    else event[:120]
                ),
                "severity": (
                    properties["severity"][:40]
                    if isinstance(properties.get("severity"), str)
                    else "Unknown"
                ),
                "sent": (
                    properties["sent"][:40]
                    if isinstance(properties.get("sent"), str)
                    else None
                ),
                "expires": (
                    properties["expires"][:40]
                    if isinstance(properties.get("expires"), str)
                    else None
                ),
            }
        )
    updated = payload.get("updated")
    return {
        "alerts": alerts,
        "skipped_alert_count": skipped_alert_count,
        "possibly_truncated": len(features) >= 50,
        "updated": updated if isinstance(updated, str) else None,
        "retrieved_at": _utc_now().isoformat(),
    }


def fetch_nws_alerts() -> dict[str, Any]:
    _, zone = _fetch_nws_grid()
    payload = _request_json(
        f"https://api.weather.gov/alerts/active?{urlencode({'zone': zone})}"
    )
    return normalize_nws_alerts(payload)


def normalize_floodnet_records(
    event_rows: Any,
    sensor_rows: Any,
    *,
    retrieved_at: datetime | None = None,
) -> dict[str, Any]:
    if not isinstance(event_rows, list) or not isinstance(sensor_rows, list):
        raise DataSourceError("NYC Open Data returned an invalid FloodNet response.")

    latest_by_sensor: dict[str, dict[str, Any]] = {}
    skipped_event_count = 0
    for row in event_rows[:100]:
        if not isinstance(row, dict):
            skipped_event_count += 1
            continue
        sensor_id = row.get("sensor_id")
        event_time = row.get("flood_start_time")
        if (
            not isinstance(sensor_id, str)
            or re.fullmatch(r"Q-[a-z0-9-]{1,90}", sensor_id) is None
            or not isinstance(event_time, str)
        ):
            skipped_event_count += 1
            continue
        try:
            parsed_event_time = datetime.fromisoformat(event_time)
        except ValueError:
            skipped_event_count += 1
            continue
        previous = latest_by_sensor.get(sensor_id)
        if previous is None or event_time > previous["flood_start_time"]:
            latest_by_sensor[sensor_id] = {
                **row,
                "_event_timestamp_has_timezone": parsed_event_time.tzinfo is not None,
            }

    sensor_metadata: dict[str, dict[str, Any]] = {}
    for row in sensor_rows[:100]:
        if not isinstance(row, dict):
            continue
        sensor_id = row.get("sensor_id")
        if (
            isinstance(sensor_id, str)
            and sensor_id in latest_by_sensor
            and row.get("borough") == "Queens"
        ):
            sensor_metadata[sensor_id] = row

    features: list[dict[str, Any]] = []
    for sensor_id, event in latest_by_sensor.items():
        sensor = sensor_metadata.get(sensor_id)
        if sensor is None:
            continue
        try:
            longitude = float(sensor["longitude"])
            latitude = float(sensor["latitude"])
            depth_inches = float(event["max_depth_inches"])
            duration_minutes = float(event["duration_mins"])
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        if (
            not _valid_number(longitude, minimum=-74.3, maximum=-73.5)
            or not _valid_number(latitude, minimum=40.4, maximum=41.0)
            or not _valid_number(depth_inches, minimum=0, maximum=200)
            or not _valid_number(duration_minutes, minimum=0, maximum=10_080)
        ):
            continue
        sensor_name = sensor.get("sensor_name")
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude],
                },
                "properties": {
                    "sensor_id": sensor_id,
                    "sensor_name": (
                        sensor_name[:120]
                        if isinstance(sensor_name, str)
                        else "Queens FloodNet sensor"
                    ),
                    "event_time": event["flood_start_time"],
                    "max_depth_inches": depth_inches,
                    "duration_minutes": duration_minutes,
                    "event_timestamp_has_timezone": event[
                        "_event_timestamp_has_timezone"
                    ],
                    "observation_type": "Historical QC-reviewed sensor event",
                },
            }
        )

    if latest_by_sensor and not features and sensor_rows:
        raise DataSourceError("FloodNet records could not be matched to valid Queens sensors.")
    fetched_at = retrieved_at or _utc_now()
    if fetched_at.tzinfo is None:
        raise ValueError("The retrieval timestamp must include a timezone.")
    return {
        "type": "FeatureCollection",
        "features": features,
        "feature_count": len(features),
        "skipped_event_count": skipped_event_count,
        "unmatched_sensor_count": len(latest_by_sensor) - len(features),
        "retrieved_at": fetched_at.astimezone(timezone.utc).isoformat(),
        "latest_event_time": max(
            (feature["properties"]["event_time"] for feature in features),
            default=None,
        ),
        "dataset_timestamp_has_timezone": (
            all(
                feature["properties"]["event_timestamp_has_timezone"]
                for feature in features
            )
            if features
            else False
        ),
    }


def fetch_floodnet_events() -> dict[str, Any]:
    event_query = urlencode(
        {
            "$select": (
                "sensor_id,sensor_name,flood_start_time,max_depth_inches,"
                "duration_mins"
            ),
            "$where": "sensor_id like 'Q-%'",
            "$order": "flood_start_time DESC",
            "$limit": "100",
        }
    )
    event_rows = _request_json(f"{FLOODNET_EVENTS_URL}?{event_query}")
    if not isinstance(event_rows, list):
        raise DataSourceError("NYC Open Data returned an invalid FloodNet event list.")
    sensor_ids = sorted(
        {
            row["sensor_id"]
            for row in event_rows[:100]
            if isinstance(row, dict)
            and isinstance(row.get("sensor_id"), str)
            and re.fullmatch(r"Q-[a-z0-9-]{1,90}", row["sensor_id"])
        }
    )
    if not sensor_ids:
        return normalize_floodnet_records(event_rows, [])

    id_list = ",".join(f"'{sensor_id}'" for sensor_id in sensor_ids)
    sensor_query = urlencode(
        {
            "$select": "sensor_id,sensor_name,longitude,latitude,borough",
            "$where": f"sensor_id in ({id_list}) AND borough='Queens'",
            "$limit": "100",
        }
    )
    sensor_rows = _request_json(f"{FLOODNET_SENSORS_URL}?{sensor_query}")
    return normalize_floodnet_records(event_rows, sensor_rows)


def parse_source_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)
