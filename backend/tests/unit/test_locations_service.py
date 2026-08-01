"""
Unit tests for LocationService — isolated from HTTP plumbing, calling the
service layer directly against the real (in-memory) database. The reverse
geocode network call is monkeypatched, matching the same pattern used by
the integration test in test_location_api.py.
"""

import pytest
from app.api import locations as locations_pkg
from app.api.locations.service import LocationService
from app.extensions import db
from app.models.city import City
from app.models.city_pincode import CityPincode
from app.models.complaint import Complaint
from app.models.role import Role
from app.models.user import User


def _ensure_city(name: str, state: str = "Test State") -> City:
    city = City.query.filter_by(name=name).first()
    if not city:
        city = City(name=name, state=state, is_active=True)
        db.session.add(city)
        db.session.commit()
    return city


def _ensure_pincode(pincode: str, city: City, area_name: str = None) -> CityPincode:
    mapping = CityPincode.query.filter_by(pincode=pincode, city_id=city.id).first()
    if not mapping:
        mapping = CityPincode(
            pincode=pincode, city_id=city.id, area_name=area_name,
            district=city.name, state=city.state, is_active=True,
        )
        db.session.add(mapping)
        db.session.commit()
    return mapping


class TestLocationServiceLookupPincode:
    """Unit tests for lookup_pincode."""

    def test_lookup_pincode_returns_unique_match(self, app):
        with app.app_context():
            city = _ensure_city("UnitLocCity1")
            _ensure_pincode("500001", city, area_name="Central")
            result = LocationService.lookup_pincode("500001")
            assert result["match_count"] == 1
            assert result["cities"][0]["city_name"] == "UnitLocCity1"

    def test_lookup_pincode_returns_multiple_matches(self, app):
        with app.app_context():
            city_a = _ensure_city("UnitLocCity2A")
            city_b = _ensure_city("UnitLocCity2B")
            _ensure_pincode("500002", city_a)
            _ensure_pincode("500002", city_b)
            result = LocationService.lookup_pincode("500002")
            assert result["match_count"] == 2

    def test_lookup_pincode_returns_zero_matches_for_unknown_pincode(self, app):
        with app.app_context():
            result = LocationService.lookup_pincode("000000")
            assert result["match_count"] == 0
            assert result["cities"] == []


class TestLocationServiceSearchCities:
    """Unit tests for search_cities."""

    def test_search_cities_filters_by_query(self, app):
        with app.app_context():
            _ensure_city("UnitSearchableCity")
            result = LocationService.search_cities("UnitSearchable")
            assert any(c["name"] == "UnitSearchableCity" for c in result["items"])

    def test_search_cities_returns_all_when_no_query(self, app):
        with app.app_context():
            result = LocationService.search_cities(None, limit=5)
            assert result["count"] <= 5

    def test_search_cities_respects_limit_bounds(self, app):
        with app.app_context():
            result = LocationService.search_cities(None, limit=0)
            assert result["count"] <= 1


class TestLocationServiceSearchPincodePrefix:
    """Unit tests for search_pincode_prefix."""

    def test_search_pincode_prefix_returns_matches(self, app):
        with app.app_context():
            city = _ensure_city("UnitLocCity3")
            _ensure_pincode("560011", city, area_name="Whitefield")
            result = LocationService.search_pincode_prefix("5600")
            assert result["count"] >= 1
            assert any(item["pincode"] == "560011" for item in result["items"])

    def test_search_pincode_prefix_too_short_returns_empty(self, app):
        with app.app_context():
            result = LocationService.search_pincode_prefix("5")
            assert result["items"] == []
            assert result["count"] == 0

    def test_search_pincode_prefix_non_digit_returns_empty(self, app):
        with app.app_context():
            result = LocationService.search_pincode_prefix("ab")
            assert result["items"] == []


class TestLocationServicePublicOverview:
    """Unit tests for get_public_overview."""

    def test_get_public_overview_returns_expected_keys(self, app):
        with app.app_context():
            result = LocationService.get_public_overview()
            for key in (
                "registered_users", "open_complaints", "resolved_complaints",
                "total_complaints", "pincode_coverage", "city_coverage",
            ):
                assert key in result


class TestLocationServiceComplaintPins:
    """Unit tests for get_public_complaint_pins."""

    def test_get_public_complaint_pins_only_returns_geocoded_complaints(self, app):
        with app.app_context():
            role = Role.query.filter_by(name=Role.CITIZEN).first()
            citizen = User.query.filter_by(email="unit.loc.pins.citizen@example.com").first()
            if not citizen:
                citizen = User(
                    username="unit_loc_pins_citizen", email="unit.loc.pins.citizen@example.com",
                    first_name="Pin", last_name="Tester", role_id=role.id, is_active=True,
                )
                citizen.set_password("Citizen@123")
                db.session.add(citizen)
                db.session.commit()

            with_coords = Complaint(
                citizen_id=citizen.id, title="Geocoded pothole",
                description="Has coordinates.", category=Complaint.CATEGORY_POTHOLE,
                status=Complaint.STATUS_PENDING, priority="medium",
                latitude=12.9716, longitude=77.5946,
            )
            without_coords = Complaint(
                citizen_id=citizen.id, title="Non-geocoded pothole",
                description="No coordinates.", category=Complaint.CATEGORY_POTHOLE,
                status=Complaint.STATUS_PENDING, priority="medium",
            )
            db.session.add_all([with_coords, without_coords])
            db.session.commit()

            result = LocationService.get_public_complaint_pins(limit=1000)
            ids = [item["id"] for item in result["items"]]
            assert with_coords.id in ids
            assert without_coords.id not in ids


class TestLocationServiceReverseGeocode:
    """Unit tests for reverse_geocode (network call monkeypatched)."""

    def test_reverse_geocode_rejects_invalid_coordinates(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="valid coordinate"):
                LocationService.reverse_geocode(999, 999)

    def test_reverse_geocode_raises_when_lookup_fails(self, app, monkeypatch):
        with app.app_context():
            monkeypatch.setattr(
                locations_pkg.service, "fetch_reverse_geocode_payload", lambda lat, lon: None
            )
            with pytest.raises(ValueError, match="Could not resolve location"):
                LocationService.reverse_geocode(26.8467, 80.9462)

    def test_reverse_geocode_returns_resolved_location(self, app, monkeypatch):
        with app.app_context():
            city = _ensure_city("UnitReverseGeoCity")
            _ensure_pincode("226010", city, area_name="Gomti Nagar")

            def fake_fetch(lat, lon):
                return {
                    "display_name": "Gomti Nagar, Lucknow, Uttar Pradesh",
                    "address": {
                        "postcode": "226010",
                        "city": "UnitReverseGeoCity",
                        "state": "Test State",
                        "suburb": "Gomti Nagar",
                    },
                }

            monkeypatch.setattr(locations_pkg.service, "fetch_reverse_geocode_payload", fake_fetch)
            result = LocationService.reverse_geocode(26.8467, 80.9462)
            assert result["pincode"] == "226010"
            assert result["city_id"] is not None
