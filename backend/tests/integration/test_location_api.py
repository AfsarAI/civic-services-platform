"""Integration tests for location lookup endpoints."""

import app.api.locations.service as location_service_module

from app.extensions import db
from app.models.complaint import Complaint
from app.models.role import Role
from app.models.user import User


class TestLocationEndpoints:
    def test_lookup_pincode_returns_city_options(self, client):
        response = client.get("/api/v1/locations/pincode/226001")
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        assert payload["data"]["pincode"] == "226001"
        assert payload["data"]["match_count"] >= 1

    def test_lookup_invalid_pincode_returns_400(self, client):
        response = client.get("/api/v1/locations/pincode/22")
        payload = response.get_json()

        assert response.status_code == 400
        assert payload["success"] is False

    def test_city_search_returns_items(self, client):
        response = client.get("/api/v1/locations/cities?query=luck")
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        assert payload["data"]["count"] >= 1

    def test_pincode_prefix_search_returns_suggestions(self, client):
        response = client.get("/api/v1/locations/pincodes?prefix=22&limit=5")
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        assert payload["data"]["prefix"] == "22"
        assert payload["data"]["count"] >= 1

    def test_pincode_prefix_search_short_prefix_returns_empty(self, client):
        response = client.get("/api/v1/locations/pincodes?prefix=2")
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        assert payload["data"]["count"] == 0

    def test_public_overview_returns_metrics(self, client):
        response = client.get("/api/v1/locations/overview")
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        assert "registered_users" in payload["data"]
        assert "open_complaints" in payload["data"]

    def test_public_complaint_pins_returns_coordinate_items(self, client):
        role = Role.query.filter_by(name=Role.CITIZEN).first()
        user = User(
            username="mapuser",
            email="mapuser@example.com",
            first_name="Map",
            last_name="User",
            role_id=role.id,
        )
        user.set_password("Password@123")
        db.session.add(user)
        db.session.flush()

        complaint = Complaint(
            title="Pothole near crossing",
            description="Large pothole causing traffic.",
            category=Complaint.CATEGORY_POTHOLE,
            status=Complaint.STATUS_PENDING,
            priority="high",
            latitude=28.6139,
            longitude=77.2090,
            citizen_id=user.id,
            pincode="110001",
        )
        db.session.add(complaint)
        db.session.commit()

        response = client.get("/api/v1/locations/complaint-pins?limit=50")
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        assert payload["data"]["count"] >= 1
        assert "latitude" in payload["data"]["items"][0]

    def test_reverse_geocode_returns_location_payload(self, client, monkeypatch):
        def _fake_reverse_lookup(_lat, _lon):
            return {
                "display_name": "Connaught Place, New Delhi, Delhi, 110001, India",
                "address": {
                    "city": "New Delhi",
                    "state": "Delhi",
                    "state_district": "New Delhi",
                    "suburb": "Connaught Place",
                    "postcode": "110001",
                },
            }

        monkeypatch.setattr(location_service_module, "fetch_reverse_geocode_payload", _fake_reverse_lookup)

        response = client.get("/api/v1/locations/reverse-geocode?lat=28.6329&lon=77.2195")
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        assert payload["data"]["pincode"] == "110001"
        assert "city_options" in payload["data"]

    def test_reverse_geocode_invalid_coordinates_return_400(self, client):
        response = client.get("/api/v1/locations/reverse-geocode?lat=181&lon=77.2")
        payload = response.get_json()

        assert response.status_code == 400
        assert payload["success"] is False
