"""
Integration tests for the admin complaint status-transition workflow
(TPS-81 Prioritize, TPS-82 Monitor Progress, TPS-83 Verify Resolution,
TPS-84 Close Complaint) and the notification events fired alongside it
(TPS-91..94, TPS-76, TPS-93).
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.api.administrator.service import AdminService
from app.api.notifications.service import NotificationService
from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.audit_log import AuditLog
from app.models.city import City
from app.models.complaint import Complaint
from app.models.complaint_assignment import ComplaintAssignment
from app.models.complaint_verification import ComplaintVerification
from app.models.notification import Notification
from app.models.role import Role
from app.models.system_setting import SystemSetting
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

    def test_admin_monitors_assignment_progress_and_overdue_deadlines(
        self, app, client
    ):
        self._ensure_system_admin("wf-monitor-admin@example.com")
        admin_token = self._login(client, "wf-monitor-admin@example.com")
        citizen_auth = self._register_and_login_citizen(
            client, "wf-monitor-citizen@example.com"
        )
        complaint_id = self._submit_complaint(
            client,
            citizen_auth["access_token"],
            citizen_auth["user"]["city_id"],
        )
        worker_id = self._create_field_worker(app, "wf-monitor-worker@example.com")
        expected = datetime.now(timezone.utc) - timedelta(hours=2)

        assign_response = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "worker_id": worker_id,
                "expected_completion_at": expected.isoformat(),
            },
        )
        assert assign_response.status_code == 201
        created_assignment = assign_response.get_json()["data"]["assignment"]
        assert created_assignment["expected_completion_at"] is not None
        assert created_assignment["updated_at"] is not None

        response = client.get(
            "/api/v1/admin/assignments?overdue=true",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        items = response.get_json()["data"]["items"]
        monitored = next(
            item for item in items if item["complaint"]["id"] == complaint_id
        )
        assert monitored["complaint"]["priority"] == "medium"
        assert monitored["complaint"]["status"] == Complaint.STATUS_ASSIGNED
        assert monitored["worker_id"] == worker_id
        assert monitored["worker_name"] == "Field Worker"
        assert monitored["status"] == ComplaintAssignment.STATUS_ASSIGNED
        assert monitored["assigned_at"] is not None
        assert monitored["expected_completion_at"] is not None
        assert monitored["updated_at"] is not None
        assert monitored["is_overdue"] is True

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
        expected_completion = datetime(2026, 8, 15, 17, 45, tzinfo=timezone.utc)
        admin_remarks = "Carry patch material and secure traffic cones before work starts."

        # Assign
        assign_response = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "worker_id": worker_id,
                "expected_completion_at": expected_completion.isoformat(),
                "notes": admin_remarks,
            },
        )
        assert assign_response.status_code == 201
        assignment = assign_response.get_json()["data"]["assignment"]

        # Worker notified of assignment
        worker_token = self._login(client, "wf-worker3@example.com", "Password123!")
        worker_notifs = client.get(
            "/api/v1/notifications/", headers={"Authorization": f"Bearer {worker_token}"}
        ).get_json()["data"]["items"]
        assignment_notifs = [
            n
            for n in worker_notifs
            if n["notification_type"] == "complaint_assigned"
            and n.get("related_assignment_id") == assignment["id"]
        ]
        assert len(assignment_notifs) == 1
        assignment_message = assignment_notifs[0]["message"]
        assert f"Complaint #{complaint_id}" in assignment_message
        assert "Assignment Date:" in assignment_message
        assert "Assignment Time:" in assignment_message
        assert "Complaint Location:" in assignment_message
        assert "Complaint Priority: Medium" in assignment_message
        assert "Expected Completion Date:" in assignment_message
        assert "2026-08-15" in assignment_message
        assert f"Administrator Remarks: {admin_remarks}" in assignment_message
        with app.app_context():
            before_count = Notification.query.filter_by(
                user_id=worker_id,
                notification_type=Notification.TYPE_COMPLAINT_ASSIGNED,
                related_assignment_id=assignment["id"],
            ).count()
            notif_service = NotificationService()
            notif_service.send_notification(
                user_id=worker_id,
                title="New task assigned",
                message="Duplicate probe 1",
                notification_type=Notification.TYPE_COMPLAINT_ASSIGNED,
                related_complaint_id=complaint_id,
                related_assignment_id=assignment["id"],
            )
            notif_service.send_notification(
                user_id=worker_id,
                title="New task assigned",
                message="Duplicate probe 2",
                notification_type=Notification.TYPE_COMPLAINT_ASSIGNED,
                related_complaint_id=complaint_id,
                related_assignment_id=assignment["id"],
            )
            after_count = Notification.query.filter_by(
                user_id=worker_id,
                notification_type=Notification.TYPE_COMPLAINT_ASSIGNED,
                related_assignment_id=assignment["id"],
            ).count()
            assert after_count == before_count

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

        complete_response = client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/complete",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={},
        )
        assert complete_response.status_code == 200

        # Admin approves completed repair -> resolved
        resolve_response = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/verify",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"decision": "approved", "remarks": "Repair verified."},
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

    def test_rework_is_recorded_notified_and_can_later_be_approved(
        self, app, client
    ):
        admin = self._ensure_system_admin("wf-rework-admin@example.com")
        admin_token = self._login(client, "wf-rework-admin@example.com")
        citizen_auth = self._register_and_login_citizen(
            client, "wf-rework-citizen@example.com"
        )
        complaint_id = self._submit_complaint(
            client,
            citizen_auth["access_token"],
            citizen_auth["user"]["city_id"],
        )
        worker_id = self._create_field_worker(app, "wf-rework-worker@example.com")
        worker_token = self._login(
            client,
            "wf-rework-worker@example.com",
            "Password123!",
        )

        assignment = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"worker_id": worker_id},
        ).get_json()["data"]["assignment"]
        assignment_id = assignment["id"]
        client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/accept",
            headers={"Authorization": f"Bearer {worker_token}"},
        )
        client.put(
            f"/api/v1/fieldworker/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={
                "status": "in_progress",
                "notes": "Replaced the damaged road surface.",
            },
        )
        client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/complete",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={
                "evidence_url": (
                    "/api/v1/fieldworker/assignments/media/repair-one.jpg"
                )
            },
        )

        missing_remarks = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/verify",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"decision": "rework_requested"},
        )
        assert missing_remarks.status_code == 400

        with app.app_context():
            setting = SystemSetting.query.first()
            setting.notify_on_status_change = False
            db.session.commit()

        rework_response = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/verify",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "decision": "rework_requested",
                "remarks": "The edge is unfinished; seal the remaining gap.",
            },
        )
        assert rework_response.status_code == 200
        rework_data = rework_response.get_json()["data"]
        assert rework_data["complaint"]["status"] == Complaint.STATUS_IN_PROGRESS
        assert (
            rework_data["complaint"]["assignment_status"]
            == ComplaintAssignment.STATUS_IN_PROGRESS
        )
        assert rework_data["verification"]["decision"] == "rework_requested"
        assert rework_data["verification"]["complaint_id"] == complaint_id
        assert rework_data["verification"]["assignment_id"] == assignment_id
        assert rework_data["verification"]["administrator_id"] == admin.id
        first_completion = rework_data["verification"]["repair_completed_at"]

        worker_notifications = client.get(
            "/api/v1/notifications/",
            headers={"Authorization": f"Bearer {worker_token}"},
        ).get_json()["data"]["items"]
        assert any(
            "remaining gap" in notification["message"]
            for notification in worker_notifications
        )

        client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/complete",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={
                "evidence_url": (
                    "/api/v1/fieldworker/assignments/media/repair-two.jpg"
                )
            },
        )
        approval_response = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/verify",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"decision": "approved", "remarks": "Rework verified."},
        )
        assert approval_response.status_code == 200
        complaint = approval_response.get_json()["data"]["complaint"]
        assert complaint["status"] == Complaint.STATUS_RESOLVED
        assert complaint["verification_status"] == "approved"
        second_completion = approval_response.get_json()["data"][
            "verification"
        ]["repair_completed_at"]
        assert second_completion != first_completion
        assert [
            item["decision"] for item in complaint["verification_history"]
        ] == ["approved", "rework_requested"]

        with app.app_context():
            decisions = ComplaintVerification.query.filter_by(
                complaint_id=complaint_id
            ).all()
            assert len(decisions) == 2

            setting = SystemSetting.query.first()
            setting.notify_on_status_change = True
            db.session.commit()

    def test_notification_failure_rolls_back_rework_verification(
        self, app, client
    ):
        admin = self._ensure_system_admin("wf-rollback-admin@example.com")
        admin_token = self._login(client, "wf-rollback-admin@example.com")
        citizen_auth = self._register_and_login_citizen(
            client, "wf-rollback-citizen@example.com"
        )
        complaint_id = self._submit_complaint(
            client,
            citizen_auth["access_token"],
            citizen_auth["user"]["city_id"],
        )
        worker_id = self._create_field_worker(
            app, "wf-rollback-worker@example.com"
        )
        worker_token = self._login(
            client,
            "wf-rollback-worker@example.com",
            "Password123!",
        )
        assignment_id = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"worker_id": worker_id},
        ).get_json()["data"]["assignment"]["id"]
        client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/accept",
            headers={"Authorization": f"Bearer {worker_token}"},
        )
        client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/complete",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={},
        )

        with app.app_context():
            service = AdminService()
            with patch.object(
                service.notifications,
                "send_notification",
                side_effect=RuntimeError("notification insert failed"),
            ):
                with pytest.raises(RuntimeError, match="notification insert failed"):
                    service.verify_repair(
                        complaint_id,
                        admin.id,
                        {
                            "decision": "rework_requested",
                            "remarks": "Redo the incomplete repair.",
                        },
                    )

            complaint = db.session.get(Complaint, complaint_id)
            assignment = db.session.get(
                ComplaintAssignment,
                assignment_id,
            )
            assert complaint.status == Complaint.STATUS_IN_PROGRESS
            assert assignment.status == ComplaintAssignment.STATUS_COMPLETED
            assert ComplaintVerification.query.filter_by(
                complaint_id=complaint_id
            ).count() == 0
            assert Notification.query.filter(
                Notification.user_id == worker_id,
                Notification.title == "Repair rework requested",
            ).count() == 0
            assert AuditLog.query.filter_by(
                action="repair_verification_rework_requested",
                resource_id=complaint_id,
            ).count() == 0

            assignment = db.session.get(
                ComplaintAssignment,
                assignment_id,
            )
            winner = ComplaintVerification(
                complaint_id=complaint_id,
                assignment_id=assignment_id,
                administrator_id=admin.id,
                decision=ComplaintVerification.DECISION_APPROVED,
                remarks="Concurrent winner.",
                repair_completed_at=assignment.completed_at,
            )
            db.session.add(winner)
            db.session.commit()

        conflict_response = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/verify",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "decision": "rework_requested",
                "remarks": "Concurrent losing decision.",
            },
        )
        assert conflict_response.status_code == 409
        assert "already been verified" in conflict_response.get_json()[
            "message"
        ].lower()

        with app.app_context():
            complaint = db.session.get(Complaint, complaint_id)
            assignment = db.session.get(
                ComplaintAssignment,
                assignment_id,
            )
            assert complaint.status == Complaint.STATUS_IN_PROGRESS
            assert assignment.status == ComplaintAssignment.STATUS_COMPLETED
            assert ComplaintVerification.query.filter_by(
                assignment_id=assignment_id,
                repair_completed_at=assignment.completed_at,
            ).count() == 1
            assert Notification.query.filter(
                Notification.user_id == worker_id,
                Notification.title == "Repair rework requested",
            ).count() == 0
            assert AuditLog.query.filter_by(
                action="repair_verification_rework_requested",
                resource_id=complaint_id,
            ).count() == 0

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
            json={
                "status": "rejected",
                "rejection_reason": "This report is outside the municipal service area.",
            },
        )
        assert response.status_code == 200

        citizen_complaint = client.get(
            f"/api/v1/citizen/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
        ).get_json()["data"]["complaint"]
        assert citizen_complaint["rejection_reason"] == (
            "This report is outside the municipal service area."
        )

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
            json={
                "status": "rejected",
                "rejection_reason": "The reported location is outside the service area.",
            },
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
