"""
Integration tests for Field Worker API endpoints.
"""

from io import BytesIO

from app.extensions import db as _db
from app.models.complaint import Complaint
from app.models.complaint_assignment import ComplaintAssignment
from app.models.notification import Notification
from app.models.role import Role
from app.models.user import User


class TestFieldWorkerEndpoints:
    """Integration tests for /api/v1/fieldworker endpoints."""

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

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Password123!"},
        )
        assert login_response.status_code == 200
        return login_response.get_json()["data"]

    @staticmethod
    def _create_field_worker(app, email: str) -> int:
        """Create a field worker user directly (no public self-registration)."""
        with app.app_context():
            role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
            worker = User(
                username=email.split("@")[0],
                email=email,
                first_name="Field",
                last_name="Worker",
                role_id=role.id,
                is_active=True,
            )
            worker.set_password("Password123!")
            _db.session.add(worker)
            _db.session.commit()
            return worker.id

    @staticmethod
    def _login(client, email: str) -> str:
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Password123!"},
        )
        assert login_response.status_code == 200
        return login_response.get_json()["data"]["access_token"]

    @classmethod
    def _create_assignment(cls, app, client, worker_id: int) -> tuple[int, int]:
        """Create a complaint (as a fresh citizen) and assign it to worker_id."""
        citizen_email = f"citizen-{worker_id}@example.com"
        citizen_auth = cls._register_and_login_citizen(client, citizen_email)
        citizen_token = citizen_auth["access_token"]

        complaint_response = client.post(
            "/api/v1/citizen/complaints",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={
                "title": "Deep pothole blocking traffic",
                "description": "Large pothole causing two-wheeler accidents daily.",
                "category": "pothole",
                "priority": "high",
                "latitude": 26.8467,
                "longitude": 80.9462,
                "address": "Near Hazratganj crossing",
                "city_id": citizen_auth["user"]["city_id"],
                "image_url": "/api/v1/citizen/complaints/media/test-photo.jpg",
            },
        )
        assert complaint_response.status_code == 201
        complaint_id = complaint_response.get_json()["data"]["complaint"]["id"]

        with app.app_context():
            citizen = User.query.filter_by(email=citizen_email).first()
            assignment = ComplaintAssignment(
                complaint_id=complaint_id,
                worker_id=worker_id,
                assigned_by_id=citizen.id,
                status=ComplaintAssignment.STATUS_ASSIGNED,
            )
            complaint = Complaint.query.get(complaint_id)
            complaint.status = Complaint.STATUS_ASSIGNED
            _db.session.add(assignment)
            _db.session.commit()
            return assignment.id, complaint_id

    def test_assignments_list_requires_auth(self, client):
        """Assignments list endpoint requires authentication."""
        response = client.get("/api/v1/fieldworker/assignments")
        assert response.status_code == 401

    def test_dashboard_endpoint_requires_auth(self, client):
        """Dashboard endpoint requires authentication."""
        response = client.get("/api/v1/fieldworker/dashboard")
        assert response.status_code == 401

    def test_full_assignment_lifecycle(self, app, client):
        """Accept -> in_progress -> complete (with evidence) full flow."""
        worker_id = self._create_field_worker(app, "fw-lifecycle@example.com")
        worker_token = self._login(client, "fw-lifecycle@example.com")
        assignment_id, complaint_id = self._create_assignment(app, client, worker_id)

        # List assignments
        list_response = client.get(
            "/api/v1/fieldworker/assignments",
            headers={"Authorization": f"Bearer {worker_token}"},
        )
        assert list_response.status_code == 200
        assert list_response.get_json()["data"]["pagination"]["total"] >= 1
        listed_assignment = list_response.get_json()["data"]["items"][0]
        # List view must include nested complaint data (title/priority/status)
        # so the dashboard table doesn't fall back to "Complaint #<id>".
        assert listed_assignment["complaint"]["id"] == complaint_id
        assert listed_assignment["complaint"]["title"]

        # Dashboard summary's recent_assignments must also include it.
        dashboard_response = client.get(
            "/api/v1/fieldworker/dashboard",
            headers={"Authorization": f"Bearer {worker_token}"},
        )
        assert dashboard_response.status_code == 200
        recent = dashboard_response.get_json()["data"]["recent_assignments"]
        assert any(a.get("complaint", {}).get("id") == complaint_id for a in recent)

        # Get assignment details
        detail_response = client.get(
            f"/api/v1/fieldworker/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {worker_token}"},
        )
        assert detail_response.status_code == 200
        assert detail_response.get_json()["data"]["assignment"]["complaint"]["id"] == complaint_id

        # Accept
        accept_response = client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/accept",
            headers={"Authorization": f"Bearer {worker_token}"},
        )
        assert accept_response.status_code == 200
        assert accept_response.get_json()["data"]["assignment"]["status"] == "accepted"

        # Update progress -> in_progress
        progress_response = client.put(
            f"/api/v1/fieldworker/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={"status": "in_progress", "notes": "Materials ordered."},
        )
        assert progress_response.status_code == 200
        assert progress_response.get_json()["data"]["assignment"]["status"] == "in_progress"

        # Upload evidence photo
        upload_response = client.post(
            "/api/v1/fieldworker/assignments/media",
            headers={"Authorization": f"Bearer {worker_token}"},
            data={"photo": (BytesIO(b"fake-image-data"), "repair.jpg")},
            content_type="multipart/form-data",
        )
        assert upload_response.status_code == 201
        evidence_url = upload_response.get_json()["data"]["evidence_url"]
        assert evidence_url.startswith("/api/v1/fieldworker/assignments/media/")

        # Complete with evidence
        complete_response = client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/complete",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={"evidence_url": evidence_url},
        )
        assert complete_response.status_code == 200
        completed = complete_response.get_json()["data"]["assignment"]
        assert completed["status"] == "completed"
        assert completed["evidence_url"] == evidence_url

        # Complaint status intentionally stays in_progress until an admin verifies.
        with app.app_context():
            complaint = Complaint.query.get(complaint_id)
            assert complaint.status == Complaint.STATUS_IN_PROGRESS

            assignment = ComplaintAssignment.query.get(assignment_id)
            notification = Notification.query.filter_by(
                user_id=assignment.assigned_by_id,
                related_complaint_id=complaint_id,
            ).filter(Notification.title.ilike("%verif%")).order_by(Notification.id.desc()).first()
            assert notification is not None
            assert "verif" in notification.title.lower()

            # The citizen is also notified directly that repair work is done
            # (TPS-91..94 lifecycle notifications), separately from the admin's
            # verification prompt above.
            citizen_notification = Notification.query.filter_by(
                user_id=complaint.citizen_id,
                related_complaint_id=complaint_id,
            ).filter(Notification.title.ilike("%completed%")).first()
            assert citizen_notification is not None

        # Citizen-facing complaint view surfaces the completed assignment status
        # so the UI can show "awaiting verification" instead of bare "in progress".
        with app.app_context():
            citizen = User.query.join(Complaint, Complaint.citizen_id == User.id).filter(
                Complaint.id == complaint_id
            ).first()
        citizen_token = self._login(client, citizen.email)
        citizen_response = client.get(
            f"/api/v1/citizen/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert citizen_response.status_code == 200
        citizen_complaint = citizen_response.get_json()["data"]["complaint"]
        assert citizen_complaint["status"] == "in_progress"
        assert citizen_complaint["assignment_status"] == "completed"
        assert citizen_complaint["repair_completed_at"] is not None

    def test_reject_assignment_returns_complaint_to_pending(self, app, client):
        """Rejecting an assignment moves the complaint back to pending."""
        worker_id = self._create_field_worker(app, "fw-reject@example.com")
        worker_token = self._login(client, "fw-reject@example.com")
        assignment_id, complaint_id = self._create_assignment(app, client, worker_id)

        reject_response = client.put(
            f"/api/v1/fieldworker/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={"status": "rejected", "notes": "Outside my service area."},
        )
        assert reject_response.status_code == 200
        assert reject_response.get_json()["data"]["assignment"]["status"] == "rejected"

        with app.app_context():
            complaint = Complaint.query.get(complaint_id)
            assert complaint.status == Complaint.STATUS_PENDING

    def test_cannot_access_other_workers_assignment(self, app, client):
        """A field worker cannot view or act on another worker's assignment."""
        owner_id = self._create_field_worker(app, "fw-owner@example.com")
        self._login(client, "fw-owner@example.com")
        assignment_id, _ = self._create_assignment(app, client, owner_id)

        self._create_field_worker(app, "fw-other@example.com")
        other_token = self._login(client, "fw-other@example.com")

        response = client.get(
            f"/api/v1/fieldworker/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert response.status_code == 404

    def test_dashboard_summary_returns_counts(self, app, client):
        """Dashboard summary reflects assignment counts by status."""
        worker_id = self._create_field_worker(app, "fw-dashboard@example.com")
        worker_token = self._login(client, "fw-dashboard@example.com")
        self._create_assignment(app, client, worker_id)

        response = client.get(
            "/api/v1/fieldworker/dashboard",
            headers={"Authorization": f"Bearer {worker_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["total_assignments"] >= 1
        assert "by_status" in data
