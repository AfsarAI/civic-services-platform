"""
Unit tests for app.utils.geo — haversine distance and bounding box helpers.
"""

from app.utils.geo import bounding_box_deltas, haversine_distance_meters


class TestHaversineDistanceMeters:
    """Unit tests for haversine_distance_meters."""

    def test_same_point_returns_zero_distance(self):
        assert haversine_distance_meters(26.8467, 80.9462, 26.8467, 80.9462) == 0

    def test_known_short_distance_is_approximately_correct(self):
        # Roughly 100m apart at these coordinates (small latitude delta).
        distance = haversine_distance_meters(26.8467, 80.9462, 26.8476, 80.9462)
        assert 90 < distance < 110

    def test_far_apart_points_return_large_distance(self):
        # Lucknow vs Mumbai — several hundred km apart.
        distance = haversine_distance_meters(26.8467, 80.9462, 19.0760, 72.8777)
        assert distance > 800_000


class TestBoundingBoxDeltas:
    """Unit tests for bounding_box_deltas."""

    def test_returns_positive_deltas_for_positive_radius(self):
        lat_delta, lon_delta = bounding_box_deltas(26.8467, 50)
        assert lat_delta > 0
        assert lon_delta > 0

    def test_larger_radius_produces_larger_deltas(self):
        small_lat, small_lon = bounding_box_deltas(26.8467, 50)
        large_lat, large_lon = bounding_box_deltas(26.8467, 500)
        assert large_lat > small_lat
        assert large_lon > small_lon

    def test_longitude_delta_widens_near_equator_vs_high_latitude(self):
        # cos(latitude) shrinks as |latitude| grows, so the same radius maps
        # to a *larger* longitude-degree delta at high latitude than at the equator.
        _, lon_delta_equator = bounding_box_deltas(0, 100)
        _, lon_delta_high_lat = bounding_box_deltas(80, 100)
        assert lon_delta_high_lat > lon_delta_equator

    def test_bounding_box_contains_a_point_at_the_given_radius(self):
        # Sanity check: a point exactly at the (approximate) radius distance
        # north should fall within the returned latitude delta.
        radius = 100
        lat_delta, _ = bounding_box_deltas(26.8467, radius)
        target_lat = 26.8467 + (radius / 111320.0)
        assert abs(target_lat - 26.8467) <= lat_delta + 1e-9
