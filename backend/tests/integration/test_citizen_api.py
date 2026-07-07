"""
Integration tests for Citizen API endpoints.
"""

from io import BytesIO

import pytest


class TestCitizenEndpoints:
    """Integration tests for /api/v1/citizen endpoints."""

    @staticmethod
    def _register_and_login(client, email: str):
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "username": email.split("@")[0],
                "email": email,
                "password": "Password123!",
                "first_name": "Citizen",
                "last_name": "Tester",
                "pincode": "226001",
            },
        )
        assert register_response.status_code == 201

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Password123!"},
        )
        assert login_response.status_code == 200
        return login_response.get_json()["data"]

    def test_complaints_list_endpoint_exists(self, client):
        """Complaints list endpoint should exist."""
        response = client.get("/api/v1/citizen/complaints")
        assert response.status_code in (200, 401, 501)

    def test_dashboard_endpoint_exists(self, client):
        """Dashboard endpoint should exist."""
        response = client.get("/api/v1/citizen/dashboard")
        assert response.status_code in (200, 401, 501)

    def test_submit_complaint_accepts_city_id_without_pincode(self, client):
        """Complaint submission should allow explicit city_id even when pincode is absent."""
        auth_data = self._register_and_login(client, "cityonlycitizen@example.com")
        token = auth_data["access_token"]
        city_id = auth_data["user"]["city_id"]

        response = client.post(
            "/api/v1/citizen/complaints",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Dangerous pothole near market",
                "description": "Deep pothole causing bike accidents during evening traffic.",
                "category": "pothole",
                "priority": "high",
                "latitude": 26.8467,
                "longitude": 80.9462,
                "address": "Near Hazratganj crossing",
                "city_id": city_id,
                "image_url": "/api/v1/citizen/complaints/media/test-photo.jpg",
            },
        )

        payload = response.get_json()
        assert response.status_code == 201
        assert payload["success"] is True
        assert payload["data"]["complaint"]["city_id"] == city_id
        assert payload["data"]["complaint"]["pincode"] is None

    def test_upload_photo_endpoint_stores_image_and_returns_url(self, app, client):
        with app.app_context():
            auth_data = self._register_and_login(client, "photo-upload-citizen@example.com")

        response = client.post(
            "/api/v1/citizen/complaints/media",
            headers={"Authorization": f"Bearer {auth_data['access_token']}"},
            data={
                "photo": (BytesIO(b"fake-image-data"), "pothole.jpg"),
            },
            content_type="multipart/form-data",
        )

        payload = response.get_json()
        assert response.status_code == 201
        assert payload["success"] is True
        assert payload["data"]["image_url"].startswith("/api/v1/citizen/complaints/media/")
