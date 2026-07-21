"""
Integration tests for the admin complaint status-transition workflow
(TPS-81 Prioritize, TPS-82 Monitor Progress, TPS-83 Verify Resolution,
TPS-84 Close Complaint) and the notification events fired alongside it
(TPS-91..94, TPS-76, TPS-93).
"""

from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.city import City
from app.models.complaint import Complaint
from app.models.role import Role
from app.models.user import User


class TestAdminComplaintWorkflow:
    """Integration tests for admin-driven complaint status transitions."""

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

    def _submit_complaint(self, client, citizen_token: str, city_id: int) -> int:
        response = client.post(
            "/api/v1/citizen/complaints",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={
                "title": "Deep pothole on ring road",
                "description": "Large pothole causing daily traffic issues.",
                "category": "pothole",
                "priority": "medium",
                "city_id": city_id,
                "image_url": "/api/v1/citizen/complaints/media/test-photo.jpg",
            },
        )
        assert response.status_code == 201
        return response.get_json()["data"]["complaint"]["id"]

    def test_admin_can_change_priority_without_status_change(self, app, client):
        self._ensure_system_admin("wf-sysadmin1@example.com")
        admin_token = self._login(client, "wf-sysadmin1@example.com")
        citizen_auth = self._register_and_login_citizen(client, "wf-citizen1@example.com")
        complaint_id = self._submit_complaint(client, citizen_auth["access_token"], citizen_auth["user"]["city_id"])

        response = client.put(
            f"/api/v1/admin/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"priority": "urgent"},
        )
        payload = response.get_json()
        assert response.status_code == 200
        assert payload["data"]["complaint"]["priority"] == "urgent"
        assert payload["data"]["complaint"]["status"] == "pending"

    def test_cannot_resolve_pending_complaint_directly(self, app, client):
        self._ensure_system_admin("wf-sysadmin2@example.com")
        admin_token = self._login(client, "wf-sysadmin2@example.com")
        citizen_auth = self._register_and_login_citizen(client, "wf-citizen2@example.com")
        complaint_id = self._submit_complaint(client, citizen_auth["access_token"], citizen_auth["user"]["city_id"])

        response = client.put(
            f"/api/v1/admin/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "resolved"},
        )
        assert response.status_code == 400
        assert "cannot move complaint" in response.get_json()["message"].lower()

    def test_full_lifecycle_assign_progress_resolve_close_with_notifications(self, app, client):
        self._ensure_system_admin("wf-sysadmin3@example.com")
        admin_token = self._login(client, "wf-sysadmin3@example.com")
        citizen_auth = self._register_and_login_citizen(client, "wf-citizen3@example.com")
        citizen_token = citizen_auth["access_token"]
        complaint_id = self._submit_complaint(client, citizen_token, citizen_auth["user"]["city_id"])

        worker_id = self._create_field_worker(app, "wf-worker3@example.com")

        # Assign
        assign_response = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"worker_id": worker_id},
        )
        assert assign_response.status_code == 201

        # Worker notified of assignment
        worker_token = self._login(client, "wf-worker3@example.com", "Password123!")
        worker_notifs = client.get(
            "/api/v1/notifications/", headers={"Authorization": f"Bearer {worker_token}"}
        ).get_json()["data"]["items"]
        assert any(n["notification_type"] == "complaint_assigned" for n in worker_notifs)

        # Citizen notified of assignment (status update)
        citizen_notifs = client.get(
            "/api/v1/notifications/", headers={"Authorization": f"Bearer {citizen_token}"}
        ).get_json()["data"]["items"]
        assert any("assigned" in n["message"].lower() for n in citizen_notifs)

        # Worker accepts -> complaint in_progress, citizen notified
        assignment_id = client.get(
            "/api/v1/fieldworker/assignments", headers={"Authorization": f"Bearer {worker_token}"}
        ).get_json()["data"]["items"][0]["id"]
        accept_response = client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/accept",
            headers={"Authorization": f"Bearer {worker_token}"},
        )
        assert accept_response.status_code == 200

        citizen_notifs = client.get(
            "/api/v1/notifications/", headers={"Authorization": f"Bearer {citizen_token}"}
        ).get_json()["data"]["items"]
        assert any("started" in n["message"].lower() for n in citizen_notifs)

        # Admin resolves (in_progress -> resolved)
        resolve_response = client.put(
            f"/api/v1/admin/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "resolved"},
        )
        assert resolve_response.status_code == 200
        assert resolve_response.get_json()["data"]["complaint"]["resolved_at"] is not None

        citizen_notifs = client.get(
            "/api/v1/notifications/", headers={"Authorization": f"Bearer {citizen_token}"}
        ).get_json()["data"]["items"]
        assert any(n["notification_type"] == "complaint_resolved" for n in citizen_notifs)

        # Admin closes (resolved -> closed)
        close_response = client.put(
            f"/api/v1/admin/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "closed"},
        )
        assert close_response.status_code == 200
        assert close_response.get_json()["data"]["complaint"]["status"] == "closed"

        citizen_notifs = client.get(
            "/api/v1/notifications/", headers={"Authorization": f"Bearer {citizen_token}"}
        ).get_json()["data"]["items"]
        assert any("closed" in n["message"].lower() for n in citizen_notifs)

    def test_worker_completion_surfaces_pending_verification_to_admin(self, app, client):
        """Field worker completing an assignment notifies the assigning admin and
        surfaces `assignment_status`/`repair_completed_at` on the admin's complaint
        views, even though the complaint's own status stays `in_progress`."""
        self._ensure_system_admin("wf-sysadmin-verify@example.com")
        admin_token = self._login(client, "wf-sysadmin-verify@example.com")
        citizen_auth = self._register_and_login_citizen(client, "wf-citizen-verify@example.com")
        complaint_id = self._submit_complaint(
            client, citizen_auth["access_token"], citizen_auth["user"]["city_id"]
        )

        worker_id = self._create_field_worker(app, "wf-worker-verify@example.com")
        assign_response = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"worker_id": worker_id},
        )
        assert assign_response.status_code == 201

        worker_token = self._login(client, "wf-worker-verify@example.com", "Password123!")
        assignment_id = client.get(
            "/api/v1/fieldworker/assignments", headers={"Authorization": f"Bearer {worker_token}"}
        ).get_json()["data"]["items"][0]["id"]
        client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/accept",
            headers={"Authorization": f"Bearer {worker_token}"},
        )
        complete_response = client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/complete",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={},
        )
        assert complete_response.status_code == 200

        # Admin's complaint list surfaces the completed assignment.
        list_response = client.get(
            "/api/v1/admin/complaints",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert list_response.status_code == 200
        listed = next(
            c for c in list_response.get_json()["data"]["items"] if c["id"] == complaint_id
        )
        assert listed["status"] == "in_progress"
        assert listed["assignment_status"] == "completed"
        assert listed["repair_completed_at"] is not None

        # Admin's complaint detail view also surfaces it.
        detail_response = client.get(
            f"/api/v1/admin/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail_response.status_code == 200
        detail = detail_response.get_json()["data"]["complaint"]
        assert detail["assignment_status"] == "completed"

        # Admin was notified that verification is needed.
        admin_notifs = client.get(
            "/api/v1/notifications/", headers={"Authorization": f"Bearer {admin_token}"}
        ).get_json()["data"]["items"]
        assert any("verif" in n["title"].lower() for n in admin_notifs)

    def test_cannot_close_resolved_complaint_twice_removed_status(self, app, client):
        """Cannot jump straight from pending to closed."""
        self._ensure_system_admin("wf-sysadmin4@example.com")
        admin_token = self._login(client, "wf-sysadmin4@example.com")
        citizen_auth = self._register_and_login_citizen(client, "wf-citizen4@example.com")
        complaint_id = self._submit_complaint(client, citizen_auth["access_token"], citizen_auth["user"]["city_id"])

        response = client.put(
            f"/api/v1/admin/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "closed"},
        )
        assert response.status_code == 400

    def test_admin_can_reject_pending_complaint_and_citizen_notified(self, app, client):
        self._ensure_system_admin("wf-sysadmin5@example.com")
        admin_token = self._login(client, "wf-sysadmin5@example.com")
        citizen_auth = self._register_and_login_citizen(client, "wf-citizen5@example.com")
        citizen_token = citizen_auth["access_token"]
        complaint_id = self._submit_complaint(client, citizen_token, citizen_auth["user"]["city_id"])

        response = client.put(
            f"/api/v1/admin/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "rejected"},
        )
        assert response.status_code == 200

        citizen_notifs = client.get(
            "/api/v1/notifications/", headers={"Authorization": f"Bearer {citizen_token}"}
        ).get_json()["data"]["items"]
        assert any(
            n["notification_type"] == "status_update" and "rejected" in n["message"].lower()
            for n in citizen_notifs
        )

    def test_worker_rejection_notifies_admin_for_reassignment(self, app, client):
        """When a field worker rejects an assignment, the admin who made the
        assignment (not just the citizen) is notified so they can reassign."""
        self._ensure_system_admin("wf-sysadmin-rej@example.com")
        admin_token = self._login(client, "wf-sysadmin-rej@example.com")
        citizen_auth = self._register_and_login_citizen(client, "wf-citizen-rej@example.com")
        complaint_id = self._submit_complaint(
            client, citizen_auth["access_token"], citizen_auth["user"]["city_id"]
        )

        worker_id = self._create_field_worker(app, "wf-worker-rej@example.com")
        assign_response = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"worker_id": worker_id},
        )
        assert assign_response.status_code == 201

        worker_token = self._login(client, "wf-worker-rej@example.com", "Password123!")
        assignment_id = client.get(
            "/api/v1/fieldworker/assignments", headers={"Authorization": f"Bearer {worker_token}"}
        ).get_json()["data"]["items"][0]["id"]

        reject_response = client.put(
            f"/api/v1/fieldworker/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={"status": "rejected", "notes": "Outside my service area."},
        )
        assert reject_response.status_code == 200

        with app.app_context():
            complaint = Complaint.query.get(complaint_id)
            assert complaint.status == Complaint.STATUS_PENDING

        admin_notifs = client.get(
            "/api/v1/notifications/", headers={"Authorization": f"Bearer {admin_token}"}
        ).get_json()["data"]["items"]
        assert any(
            "reassignment" in n["message"].lower() or "reject" in n["title"].lower()
            for n in admin_notifs
        )

    def test_admin_reject_notifies_worker_and_blocks_further_worker_action(self, app, client):
        """When an admin rejects a complaint that still has an active
        assignment, the field worker is notified and can no longer act on it."""
        self._ensure_system_admin("wf-sysadmin-block@example.com")
        admin_token = self._login(client, "wf-sysadmin-block@example.com")
        citizen_auth = self._register_and_login_citizen(client, "wf-citizen-block@example.com")
        complaint_id = self._submit_complaint(
            client, citizen_auth["access_token"], citizen_auth["user"]["city_id"]
        )

        worker_id = self._create_field_worker(app, "wf-worker-block@example.com")
        client.post(
            f"/api/v1/admin/complaints/{complaint_id}/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"worker_id": worker_id},
        )
        worker_token = self._login(client, "wf-worker-block@example.com", "Password123!")
        assignment_id = client.get(
            "/api/v1/fieldworker/assignments", headers={"Authorization": f"Bearer {worker_token}"}
        ).get_json()["data"]["items"][0]["id"]
        client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/accept",
            headers={"Authorization": f"Bearer {worker_token}"},
        )

        # Admin rejects the complaint while the worker is still actively assigned.
        reject_response = client.put(
            f"/api/v1/admin/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "rejected"},
        )
        assert reject_response.status_code == 200

        worker_notifs = client.get(
            "/api/v1/notifications/", headers={"Authorization": f"Bearer {worker_token}"}
        ).get_json()["data"]["items"]
        assert any("stop work" in n["title"].lower() for n in worker_notifs)

        # The worker can no longer complete (or otherwise act on) this assignment.
        complete_response = client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/complete",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={},
        )
        assert complete_response.status_code == 400
        assert "rejected" in complete_response.get_json()["message"].lower()
