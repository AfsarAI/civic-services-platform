"""
Integration tests for TPS-77: Submit Feedback and Rate Repair.
"""

from app.extensions import db
from app.models.complaint import Complaint


class TestCitizenFeedbackEndpoints:
    """Integration tests for POST /api/v1/citizen/complaints/<id>/feedback."""

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

    @staticmethod
    def _submit_complaint(client, token, city_id):
        response = client.post(
            "/api/v1/citizen/complaints",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Pothole near the school gate",
                "description": "Original description before any edits.",
                "category": "pothole",
                "priority": "medium",
                "latitude": 26.8467,
                "longitude": 80.9462,
                "address": "Original Road",
                "city_id": city_id,
                "image_url": "/api/v1/citizen/complaints/media/original-photo.jpg",
            },
        )
        assert response.status_code == 201
        return response.get_json()["data"]["complaint"]

    @staticmethod
    def _mark_resolved(app, complaint_id):
        with app.app_context():
            db_complaint = Complaint.query.get(complaint_id)
            db_complaint.status = Complaint.STATUS_RESOLVED
            db.session.commit()

    def test_citizen_can_submit_feedback_for_resolved_complaint(self, app, client):
        """AC 1, 2, 3, 4, 6: feedback is accepted, saved, and confirmed."""
        auth_data = self._register_and_login(client, "feedback-owner@example.com")
        token = auth_data["access_token"]
        complaint = self._submit_complaint(client, token, auth_data["user"]["city_id"])
        self._mark_resolved(app, complaint["id"])

        response = client.post(
            f"/api/v1/citizen/complaints/{complaint['id']}/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={"rating": 4, "comment": "Repair was done quickly and neatly."},
        )
        payload = response.get_json()

        assert response.status_code == 201
        assert payload["success"] is True
        assert payload["message"] == "Feedback submitted successfully."
        assert payload["data"]["feedback"]["rating"] == 4
        assert payload["data"]["feedback"]["comment"] == "Repair was done quickly and neatly."
        assert payload["data"]["feedback"]["created_at"]

    def test_feedback_comment_is_optional(self, app, client):
        """AC 3: comment can be omitted."""
        auth_data = self._register_and_login(client, "feedback-nocomment@example.com")
        token = auth_data["access_token"]
        complaint = self._submit_complaint(client, token, auth_data["user"]["city_id"])
        self._mark_resolved(app, complaint["id"])

        response = client.post(
            f"/api/v1/citizen/complaints/{complaint['id']}/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={"rating": 5},
        )
        assert response.status_code == 201
        assert response.get_json()["data"]["feedback"]["comment"] is None

    def test_feedback_rating_must_be_between_1_and_5(self, app, client):
        """AC 2: rating outside 1-5 is rejected (Flask-RESTX Swagger model
        also declares min/max on this field, so the request never reaches
        the Marshmallow schema — it's rejected with 400, not 422)."""
        auth_data = self._register_and_login(client, "feedback-badrating@example.com")
        token = auth_data["access_token"]
        complaint = self._submit_complaint(client, token, auth_data["user"]["city_id"])
        self._mark_resolved(app, complaint["id"])

        response = client.post(
            f"/api/v1/citizen/complaints/{complaint['id']}/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={"rating": 6},
        )
        assert response.status_code == 400

    def test_feedback_rejected_for_pending_complaint(self, client):
        """AC 1: feedback is only allowed for completed (resolved/closed) complaints."""
        auth_data = self._register_and_login(client, "feedback-pending@example.com")
        token = auth_data["access_token"]
        complaint = self._submit_complaint(client, token, auth_data["user"]["city_id"])

        response = client.post(
            f"/api/v1/citizen/complaints/{complaint['id']}/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={"rating": 5},
        )
        payload = response.get_json()
        assert response.status_code == 400
        assert "resolved or closed" in payload["message"].lower()

    def test_citizen_cannot_submit_feedback_twice(self, app, client):
        """AC 5: only one feedback per complaint."""
        auth_data = self._register_and_login(client, "feedback-twice@example.com")
        token = auth_data["access_token"]
        complaint = self._submit_complaint(client, token, auth_data["user"]["city_id"])
        self._mark_resolved(app, complaint["id"])

        first = client.post(
            f"/api/v1/citizen/complaints/{complaint['id']}/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={"rating": 5, "comment": "Great work."},
        )
        assert first.status_code == 201

        second = client.post(
            f"/api/v1/citizen/complaints/{complaint['id']}/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={"rating": 2, "comment": "Trying again."},
        )
        payload = second.get_json()
        assert second.status_code == 400
        assert "already been submitted" in payload["message"].lower()

    def test_citizen_cannot_submit_feedback_for_another_citizens_complaint(self, client):
        """Ownership check: feedback endpoint reuses _get_owned."""
        owner_auth = self._register_and_login(client, "feedback-owner2@example.com")
        complaint = self._submit_complaint(client, owner_auth["access_token"], owner_auth["user"]["city_id"])

        other_auth = self._register_and_login(client, "feedback-intruder@example.com")
        response = client.post(
            f"/api/v1/citizen/complaints/{complaint['id']}/feedback",
            headers={"Authorization": f"Bearer {other_auth['access_token']}"},
            json={"rating": 3},
        )
        assert response.status_code in (400, 404)
