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

    # ── TPS-74: Edit Complaint (Before Assignment) ────────────────────────

    def _submit_complaint(self, client, token, city_id):
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

    def test_citizen_can_edit_own_pending_complaint(self, client):
        """AC 3 & 6: edits are saved and a confirmation message is returned."""
        auth_data = self._register_and_login(client, "edit-owner@example.com")
        token = auth_data["access_token"]
        complaint = self._submit_complaint(client, token, auth_data["user"]["city_id"])

        response = client.put(
            f"/api/v1/citizen/complaints/{complaint['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "description": "Updated description with more detail about the damage.",
                "address": "Updated Road, near the new landmark",
                "latitude": 26.9,
                "longitude": 81.0,
                "image_url": "/api/v1/citizen/complaints/media/updated-photo.jpg",
            },
        )
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        assert payload["message"] == "Complaint updated successfully."
        updated = payload["data"]["complaint"]
        assert updated["description"] == "Updated description with more detail about the damage."
        assert updated["address"] == "Updated Road, near the new landmark"
        assert updated["latitude"] == 26.9
        assert updated["longitude"] == 81.0
        assert updated["image_url"] == "/api/v1/citizen/complaints/media/updated-photo.jpg"
        assert updated["status"] == "pending"

    def test_edit_updates_last_updated_timestamp(self, client):
        """AC 4: the system records the last updated date and time."""
        auth_data = self._register_and_login(client, "edit-timestamp@example.com")
        token = auth_data["access_token"]
        complaint = self._submit_complaint(client, token, auth_data["user"]["city_id"])
        original_updated_at = complaint["updated_at"]

        response = client.put(
            f"/api/v1/citizen/complaints/{complaint['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"description": "Another revision of the description text."},
        )
        assert response.status_code == 200
        new_updated_at = response.get_json()["data"]["complaint"]["updated_at"]
        assert new_updated_at != original_updated_at

    def test_citizen_cannot_edit_another_citizens_complaint(self, client):
        """AC 1: citizens can only edit their own complaints."""
        owner_auth = self._register_and_login(client, "edit-owner2@example.com")
        complaint = self._submit_complaint(client, owner_auth["access_token"], owner_auth["user"]["city_id"])

        other_auth = self._register_and_login(client, "edit-intruder@example.com")
        response = client.put(
            f"/api/v1/citizen/complaints/{complaint['id']}",
            headers={"Authorization": f"Bearer {other_auth['access_token']}"},
            json={"description": "Trying to edit someone else's complaint."},
        )
        assert response.status_code in (400, 404)

    def test_edit_disabled_once_complaint_is_assigned(self, app, client):
        """AC 2 & 5: editing is blocked once the complaint has been assigned."""
        from app.extensions import db
        from app.models.complaint import Complaint
        from app.models.complaint_assignment import ComplaintAssignment
        from app.models.role import Role
        from app.models.user import User

        auth_data = self._register_and_login(client, "edit-assigned@example.com")
        token = auth_data["access_token"]
        complaint = self._submit_complaint(client, token, auth_data["user"]["city_id"])

        with app.app_context():
            fw_role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
            worker = User(
                username="edit_test_worker",
                email="edit-test-worker@example.com",
                first_name="Field",
                last_name="Worker",
                role_id=fw_role.id,
                is_active=True,
            )
            worker.set_password("Worker@123")
            db.session.add(worker)
            db.session.flush()

            db_complaint = Complaint.query.get(complaint["id"])
            db_complaint.status = Complaint.STATUS_ASSIGNED
            db.session.add(
                ComplaintAssignment(
                    complaint_id=complaint["id"],
                    worker_id=worker.id,
                    assigned_by_id=worker.id,
                    status=ComplaintAssignment.STATUS_ASSIGNED,
                )
            )
            db.session.commit()

        response = client.put(
            f"/api/v1/citizen/complaints/{complaint['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"description": "Trying to edit after assignment."},
        )
        payload = response.get_json()
        assert response.status_code == 400
        assert "pending" in payload["message"].lower()

    # ── TPS-75: Cancel Complaint ───────────────────────────────────────────

    def test_citizen_can_cancel_own_pending_complaint(self, client):
        """AC 3 (confirmation is a frontend concern) & AC 4 & AC 6."""
        auth_data = self._register_and_login(client, "cancel-owner@example.com")
        token = auth_data["access_token"]
        complaint = self._submit_complaint(client, token, auth_data["user"]["city_id"])

        response = client.delete(
            f"/api/v1/citizen/complaints/{complaint['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        assert payload["message"] == "Complaint cancelled successfully."
        assert payload["data"]["complaint"]["status"] == "cancelled"

    def test_cancelled_complaint_is_preserved_not_deleted(self, client):
        """AC 4: the record is preserved with status 'cancelled', not removed."""
        auth_data = self._register_and_login(client, "cancel-preserve@example.com")
        token = auth_data["access_token"]
        complaint = self._submit_complaint(client, token, auth_data["user"]["city_id"])

        client.delete(
            f"/api/v1/citizen/complaints/{complaint['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        response = client.get(
            f"/api/v1/citizen/complaints/{complaint['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.get_json()["data"]["complaint"]["status"] == "cancelled"

    def test_citizen_cannot_cancel_another_citizens_complaint(self, client):
        """AC 1: citizens can only cancel their own complaints."""
        owner_auth = self._register_and_login(client, "cancel-owner2@example.com")
        complaint = self._submit_complaint(client, owner_auth["access_token"], owner_auth["user"]["city_id"])

        other_auth = self._register_and_login(client, "cancel-intruder@example.com")
        response = client.delete(
            f"/api/v1/citizen/complaints/{complaint['id']}",
            headers={"Authorization": f"Bearer {other_auth['access_token']}"},
        )
        assert response.status_code in (400, 404)

    def test_cancel_disabled_once_complaint_is_assigned(self, app, client):
        """AC 2: complaints can only be cancelled before assignment."""
        from app.extensions import db
        from app.models.complaint import Complaint
        from app.models.complaint_assignment import ComplaintAssignment
        from app.models.role import Role
        from app.models.user import User

        auth_data = self._register_and_login(client, "cancel-assigned@example.com")
        token = auth_data["access_token"]
        complaint = self._submit_complaint(client, token, auth_data["user"]["city_id"])

        with app.app_context():
            fw_role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
            worker = User(
                username="cancel_test_worker",
                email="cancel-test-worker@example.com",
                first_name="Field",
                last_name="Worker",
                role_id=fw_role.id,
                is_active=True,
            )
            worker.set_password("Worker@123")
            db.session.add(worker)
            db.session.flush()

            db_complaint = Complaint.query.get(complaint["id"])
            db_complaint.status = Complaint.STATUS_ASSIGNED
            db.session.add(
                ComplaintAssignment(
                    complaint_id=complaint["id"],
                    worker_id=worker.id,
                    assigned_by_id=worker.id,
                    status=ComplaintAssignment.STATUS_ASSIGNED,
                )
            )
            db.session.commit()

        response = client.delete(
            f"/api/v1/citizen/complaints/{complaint['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        payload = response.get_json()
        assert response.status_code == 400
        assert "pending" in payload["message"].lower()

    def test_cancelled_complaint_cannot_be_assigned(self, app, client):
        """AC 5: cancelled complaints are never eligible for assignment."""
        from app.extensions import db
        from app.models.administrator_profile import AdministratorProfile
        from app.models.role import Role
        from app.models.user import User

        auth_data = self._register_and_login(client, "cancel-noassign@example.com")
        token = auth_data["access_token"]
        complaint = self._submit_complaint(client, token, auth_data["user"]["city_id"])

        client.delete(
            f"/api/v1/citizen/complaints/{complaint['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        with app.app_context():
            admin_role = Role.query.filter_by(name=Role.ADMINISTRATOR).first()
            fw_role = Role.query.filter_by(name=Role.FIELD_WORKER).first()

            admin = User(
                username="cancel_test_admin",
                email="cancel-test-admin@example.com",
                first_name="Sys",
                last_name="Admin",
                role_id=admin_role.id,
                is_active=True,
            )
            admin.set_password("Admin@123456")
            db.session.add(admin)
            db.session.flush()
            db.session.add(
                AdministratorProfile(
                    user_id=admin.id,
                    admin_level=AdministratorProfile.SYSTEM,
                    city_id=None,
                    created_by_id=None,
                )
            )

            worker = User(
                username="cancel_noassign_worker",
                email="cancel-noassign-worker@example.com",
                first_name="Field",
                last_name="Worker",
                role_id=fw_role.id,
                is_active=True,
            )
            worker.set_password("Worker@123")
            db.session.add(worker)
            db.session.commit()
            worker_id = worker.id

        admin_login = client.post(
            "/api/v1/auth/login", json={"email": "cancel-test-admin@example.com", "password": "Admin@123456"}
        )
        admin_token = admin_login.get_json()["data"]["access_token"]

        response = client.post(
            f"/api/v1/admin/complaints/{complaint['id']}/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"worker_id": worker_id},
        )
        assert response.status_code == 400
