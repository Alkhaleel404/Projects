"""Transparent spatial sampling for FloodNet monitoring coverage.

The grid is a sampling envelope around published Queens sensor coordinates, not a
borough boundary, flood model, or claim about where flooding occurs.
"""
from __future__ import annotations

import math
from typing import Any


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Great-circle distance in metres between (latitude, longitude) pairs."""
    radius = 6_371_000.0
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(min(1.0, math.sqrt(value)))


def normalize_sensor_locations(rows: Any) -> list[dict[str, Any]]:
    """Keep only plausible Queens sensor coordinates from the public inventory."""
    if not isinstance(rows, list):
        raise ValueError("Sensor inventory must be a list.")
    sensors: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("borough") != "Queens":
            continue
        sensor_id = row.get("sensor_id")
        try:
            lat, lon = float(row["latitude"]), float(row["longitude"])
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        if not isinstance(sensor_id, str) or not sensor_id or sensor_id in seen:
            continue
        if not (40.45 <= lat <= 40.82 and -73.96 <= lon <= -73.70):
            continue
        seen.add(sensor_id)
        name = row.get("sensor_name")
        sensors.append({
            "sensor_id": sensor_id,
            "name": name[:120] if isinstance(name, str) else sensor_id,
            "lat": lat,
            "lon": lon,
        })
    return sorted(sensors, key=lambda sensor: sensor["sensor_id"])


def sample_monitoring_gaps(
    sensors: list[dict[str, Any]], *, step_degrees: float = 0.008
) -> dict[str, Any]:
    """Sample a regular grid inside the sensors' coordinate envelope.

    Distances describe proximity to the nearest listed sensor only. The envelope
    can include water and non-residential land; it is not a borough-wide coverage
    percentage or an estimate of flood risk.
    """
    if not sensors:
        raise ValueError("No valid Queens sensor locations are available.")
    if not (0.002 <= step_degrees <= 0.02):
        raise ValueError("Grid spacing must be between 0.002 and 0.02 degrees.")
    lats = [float(sensor["lat"]) for sensor in sensors]
    lons = [float(sensor["lon"]) for sensor in sensors]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    if min_lat == max_lat:
        min_lat -= step_degrees
        max_lat += step_degrees
    if min_lon == max_lon:
        min_lon -= step_degrees
        max_lon += step_degrees

    lat_count = min(60, max(2, math.ceil((max_lat - min_lat) / step_degrees) + 1))
    lon_count = min(60, max(2, math.ceil((max_lon - min_lon) / step_degrees) + 1))
    points = []
    for iy in range(lat_count):
        lat = min_lat + (max_lat - min_lat) * iy / (lat_count - 1)
        for ix in range(lon_count):
            lon = min_lon + (max_lon - min_lon) * ix / (lon_count - 1)
            nearest = min(
                sensors,
                key=lambda sensor: haversine_m((lat, lon), (sensor["lat"], sensor["lon"])),
            )
            distance = haversine_m((lat, lon), (nearest["lat"], nearest["lon"]))
            points.append({
                "lat": lat, "lon": lon, "nearest_sensor": nearest["name"],
                "distance_m": round(distance),
                "band": "Within 1 km" if distance <= 1000 else (
                    "1–2 km" if distance <= 2000 else "Over 2 km"
                ),
            })
    distances = [point["distance_m"] for point in points]
    return {
        "sensor_count": len(sensors),
        "sample_count": len(points),
        "points": points,
        "nearest_distance_m": min(distances),
        "median_distance_m": sorted(distances)[len(distances) // 2],
        "over_2km_count": sum(distance > 2000 for distance in distances),
        "envelope": [min_lat, min_lon, max_lat, max_lon],
        "step_degrees": step_degrees,
    }
