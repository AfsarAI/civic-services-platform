"""
Geo utilities — distance calculations used for duplicate-complaint detection.
"""

import math

EARTH_RADIUS_METERS = 6371000.0


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance between two coordinates, in meters."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_METERS * c


def bounding_box_deltas(latitude: float, radius_meters: float) -> tuple[float, float]:
    """Return ``(lat_delta_degrees, lon_delta_degrees)`` for a cheap SQL
    pre-filter bounding box around ``latitude`` at the given radius.

    Deliberately generous — exact filtering happens afterwards via
    ``haversine_distance_meters``.
    """
    lat_delta = radius_meters / 111320.0
    lon_delta = radius_meters / (111320.0 * max(math.cos(math.radians(latitude)), 0.01))
    return lat_delta, lon_delta
