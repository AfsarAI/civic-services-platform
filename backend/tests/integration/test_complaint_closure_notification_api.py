"""
Integration tests for TPS-94: Receive Complaint Closure Notifications.
"""

from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.city import City
from app.models.role import Role
from app.models.user import User


class TestComplaintClosureNotification:
    """Integration tests covering the citizen notification sent on complaint closure."""

    @staticmethod
    def _ensure_system_admin(email: str) -> User:
        role = Role.query.filter_by(name=Role.ADMINISTRATOR).first()
        user = User.query.filter_by(email=email).first()
        if user:
            return user
        user = User(
            username=email.split("@")[0],
            email=email,
            first_name="System",
            last_name="Admin",
            role_id=role.id,
            is_active=True,
        )
        user.set_password("Admin@123456")
        db.session.add(user)
        db.session.flush()
        db.session.add(
            AdministratorProfile(
                user_id=user.id,
                admin_level=AdministratorProfile.SYSTEM,
                city_id=None,
                created_by_id=None,
            )
        )
        db.session.commit()
        return user

    @staticmethod
    def _login(client, email: str, password: str = "Admin@123456") -> str:
        response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200
        return response.get_json()["data"]["access_token"]

    @staticmethod
    def _register_and_login_citizen(client, email: str):
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
        login_response = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
        assert login_response.status_code == 200
        return login_response.get_json()["data"]

    @staticmethod
    def _create_field_worker(app, email: str, city_name: str = "Lucknow") -> int:
        with app.app_context():
            city = City.query.filter_by(name=city_name).first()
            if not city:
                city = City(name=city_name, is_active=True)
                db.session.add(city)
                db.session.flush()

            role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
            worker = User(
                username=email.split("@")[0],
                email=email,
                first_name="Field",
                last_name="Worker",
                role_id=role.id,
                city_id=city.id,
                is_active=True,
            )
            worker.set_password("Password123!")
            db.session.add(worker)
            db.session.commit()
            return worker.id

    @staticmethod
    def _submit_complaint(client, citizen_token: str, city_id: int) -> int:
        response = client.post(
            "/api/v1/citizen/complaints",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={
                "title": "Deep pothole near the market",
                "description": "Large pothole causing daily traffic issues.",
                "category": "pothole",
                "priority": "medium",
                "city_id": city_id,
                "image_url": "/api/v1/citizen/complaints/media/test-photo.jpg",
            },
        )
        assert response.status_code == 201
        return response.get_json()["data"]["complaint"]["id"]

    def _drive_complaint_to_closed(self, app, client, prefix: str):
        """Register a citizen, submit a complaint, and push it through the full
        assign -> accept -> complete -> verify (approve) -> close lifecycle.

        Returns (citizen_token, admin_token, complaint_id).
        """
        self._ensure_system_admin(f"{prefix}-admin@example.com")
        admin_token = self._login(client, f"{prefix}-admin@example.com")
        citizen_auth = self._register_and_login_citizen(client, f"{prefix}-citizen@example.com")
        citizen_token = citizen_auth["access_token"]
        complaint_id = self._submit_complaint(client, citizen_token, citizen_auth["user"]["city_id"])

        worker_id = self._create_field_worker(app, f"{prefix}-worker@example.com")

        assign_response = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"worker_id": worker_id},
        )
        assert assign_response.status_code == 201

        worker_token = self._login(client, f"{prefix}-worker@example.com", "Password123!")
        assignment_id = client.get(
            "/api/v1/fieldworker/assignments", headers={"Authorization": f"Bearer {worker_token}"}
        ).get_json()["data"]["items"][0]["id"]

        accept_response = client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/accept",
            headers={"Authorization": f"Bearer {worker_token}"},
        )
        assert accept_response.status_code == 200

        complete_response = client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/complete",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={},
        )
        assert complete_response.status_code == 200

        verify_response = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/verify",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"decision": "approved", "remarks": "Repair verified."},
        )
        assert verify_response.status_code == 200

        close_response = client.put(
            f"/api/v1/admin/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "closed"},
        )
        assert close_response.status_code == 200

        return citizen_token, admin_token, complaint_id

    @staticmethod
    def _closure_notification(client, citizen_token: str, complaint_id: int) -> dict:
        notifs = client.get(
            "/api/v1/notifications/", headers={"Authorization": f"Bearer {citizen_token}"}
        ).get_json()["data"]["items"]
        return next(n for n in notifs if "closed" in n["message"].lower() and str(complaint_id) in n["message"])

    def test_closure_sets_closed_at_timestamp(self, app, client):
        """AC3: closing a complaint records its own closure timestamp, set no
        earlier than resolution (verify and close are separate lifecycle
        events, even though both can land in the same wall-clock tick when
        driven back-to-back in-process, as this test does)."""
        from datetime import datetime

        citizen_token, admin_token, complaint_id = self._drive_complaint_to_closed(app, client, "close-ts")

        response = client.get(
            f"/api/v1/citizen/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        complaint = response.get_json()["data"]["complaint"]

        assert complaint["closed_at"] is not None
        assert complaint["resolved_at"] is not None
        closed_at = datetime.fromisoformat(complaint["closed_at"])
        resolved_at = datetime.fromisoformat(complaint["resolved_at"])
        assert closed_at >= resolved_at

    def test_closure_notification_contains_complaint_id(self, app, client):
        """AC2 regression guard: closure notification references the complaint ID."""
        citizen_token, _admin_token, complaint_id = self._drive_complaint_to_closed(app, client, "close-id")

        notification = self._closure_notification(client, citizen_token, complaint_id)
        assert f"#{complaint_id}" in notification["message"]

    def test_closure_notification_contains_closure_date(self, app, client):
        """AC3: closure notification message includes the formatted closure date."""
        citizen_token, _admin_token, complaint_id = self._drive_complaint_to_closed(app, client, "close-date")

        response = client.get(
            f"/api/v1/citizen/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        closed_at_iso = response.get_json()["data"]["complaint"]["closed_at"]
        from datetime import datetime

        expected_date_str = datetime.fromisoformat(closed_at_iso).strftime("%B %d, %Y")

        notification = self._closure_notification(client, citizen_token, complaint_id)
        assert expected_date_str in notification["message"]

    def test_closure_notification_contains_feedback_prompt(self, app, client):
        """AC4: closure notification prompts feedback, and carries the complaint
        link target (related_complaint_id) the frontend uses to route there."""
        citizen_token, _admin_token, complaint_id = self._drive_complaint_to_closed(app, client, "close-fb")

        notification = self._closure_notification(client, citizen_token, complaint_id)
        assert "feedback" in notification["message"].lower()
        assert notification["related_complaint_id"] == complaint_id

    def test_closure_notification_appears_in_notification_center(self, app, client):
        """AC5 regression guard: closure notification is retrievable via the
        general notifications listing endpoint."""
        citizen_token, _admin_token, complaint_id = self._drive_complaint_to_closed(app, client, "close-center")

        response = client.get(
            "/api/v1/notifications/", headers={"Authorization": f"Bearer {citizen_token}"}
        )
        assert response.status_code == 200
        assert any(
            "closed" in n["message"].lower() and str(complaint_id) in n["message"]
            for n in response.get_json()["data"]["items"]
        )

    def test_closure_notification_can_be_marked_read(self, app, client):
        """AC6 regression guard: the closure notification can be marked as read."""
        citizen_token, _admin_token, complaint_id = self._drive_complaint_to_closed(app, client, "close-read")

        notification = self._closure_notification(client, citizen_token, complaint_id)
        response = client.patch(
            f"/api/v1/notifications/{notification['id']}/read",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        payload = response.get_json()
        assert response.status_code == 200
        assert payload["data"]["notification"]["is_read"] is True
        assert payload["data"]["notification"]["read_at"] is not None

    def test_serializer_exposes_closed_at_on_citizen_and_admin_views(self, app, client):
        """closed_at is consistent between the citizen's and admin's complaint views."""
        citizen_token, admin_token, complaint_id = self._drive_complaint_to_closed(app, client, "close-views")

        citizen_view = client.get(
            f"/api/v1/citizen/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
        ).get_json()["data"]["complaint"]
        admin_view = client.get(
            f"/api/v1/admin/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        ).get_json()["data"]["complaint"]

        assert citizen_view["closed_at"] is not None
        assert citizen_view["closed_at"] == admin_view["closed_at"]
