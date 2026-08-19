"""
Integration tests for system-wide settings (TPS-99: Configure System Settings).
"""

from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.audit_log import AuditLog
from app.models.role import Role
from app.models.user import User


class TestSystemSettingsEndpoints:
    """Integration tests for GET/PUT /api/v1/admin/settings."""

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
        client.post(
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
        login_response = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
        assert login_response.status_code == 200
        return login_response.get_json()["data"]["access_token"]

    def _reset_settings(self, client, admin_token: str):
        """Restore default settings so other tests aren't affected."""
        client.put(
            "/api/v1/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"maintenance_mode": False, "notify_on_status_change": True},
        )

    def test_non_system_admin_cannot_access_settings(self, app, client):
        citizen_token = self._register_and_login_citizen(client, "settings-citizen@example.com")
        response = client.get(
            "/api/v1/admin/settings", headers={"Authorization": f"Bearer {citizen_token}"}
        )
        assert response.status_code == 403

    def test_get_settings_returns_defaults(self, app, client):
        self._ensure_system_admin("settings-admin1@example.com")
        token = self._login(client, "settings-admin1@example.com")

        response = client.get("/api/v1/admin/settings", headers={"Authorization": f"Bearer {token}"})
        payload = response.get_json()
        assert response.status_code == 200
        assert payload["data"]["settings"]["site_name"]
        assert payload["data"]["settings"]["maintenance_mode"] is False
        assert payload["data"]["settings"]["notify_on_status_change"] is True

    def test_update_settings_persists_changes_and_logs_audit(self, app, client):
        self._ensure_system_admin("settings-admin2@example.com")
        token = self._login(client, "settings-admin2@example.com")

        response = client.put(
            "/api/v1/admin/settings",
            headers={"Authorization": f"Bearer {token}"},
            json={"site_name": "Test City Services", "support_email": "help@example.com"},
        )
        payload = response.get_json()
        assert response.status_code == 200
        assert payload["data"]["settings"]["site_name"] == "Test City Services"
        assert payload["data"]["settings"]["support_email"] == "help@example.com"

        # Persisted for subsequent GETs
        get_response = client.get("/api/v1/admin/settings", headers={"Authorization": f"Bearer {token}"})
        assert get_response.get_json()["data"]["settings"]["site_name"] == "Test City Services"

        with app.app_context():
            audit_entry = (
                AuditLog.query.filter_by(action="system_settings_updated")
                .order_by(AuditLog.created_at.desc())
                .first()
            )
            assert audit_entry is not None
            assert "site_name" in audit_entry.details["updated_fields"]

    def test_update_settings_rejects_invalid_priority(self, app, client):
        self._ensure_system_admin("settings-admin3@example.com")
        token = self._login(client, "settings-admin3@example.com")

        response = client.put(
            "/api/v1/admin/settings",
            headers={"Authorization": f"Bearer {token}"},
            json={"default_complaint_priority": "critical"},
        )
        assert response.status_code == 400

    def test_update_settings_rejects_invalid_email(self, app, client):
        self._ensure_system_admin("settings-admin4@example.com")
        token = self._login(client, "settings-admin4@example.com")

        response = client.put(
            "/api/v1/admin/settings",
            headers={"Authorization": f"Bearer {token}"},
            json={"support_email": "not-an-email"},
        )
        assert response.status_code == 422

    def test_default_complaint_priority_applies_to_new_complaints(self, app, client):
        """`default_complaint_priority` (TPS-99, AC3) must take effect immediately:
        a complaint submitted without an explicit priority picks up whatever the
        system admin has configured, not a hardcoded 'medium'."""
        admin_token = self._login(client, self._ensure_system_admin("settings-admin5@example.com").email)
        update_response = client.put(
            "/api/v1/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"default_complaint_priority": "urgent"},
        )
        assert update_response.status_code == 200
        assert update_response.get_json()["data"]["settings"]["default_complaint_priority"] == "urgent"

        citizen_token = self._register_and_login_citizen(client, "settings-citizen-priority@example.com")
        complaint_response = client.post(
            "/api/v1/citizen/complaints",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={
                "title": "Deep pothole near school gate",
                "description": "Large pothole causing daily traffic issues near the school.",
                "category": "pothole",
                "image_url": "/api/v1/citizen/complaints/media/test-photo.jpg",
            },
        )
        assert complaint_response.status_code == 201
        assert complaint_response.get_json()["data"]["complaint"]["priority"] == "urgent"

        # An explicit priority from the citizen still overrides the configured default.
        override_response = client.post(
            "/api/v1/citizen/complaints",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={
                "title": "Minor crack on sidewalk",
                "description": "Small crack, not urgent but worth noting for repair.",
                "category": "pothole",
                "priority": "low",
                "image_url": "/api/v1/citizen/complaints/media/test-photo2.jpg",
            },
        )
        assert override_response.status_code == 201
        assert override_response.get_json()["data"]["complaint"]["priority"] == "low"

    def test_maintenance_mode_blocks_non_admin_login_but_not_admin(self, app, client):
        self._ensure_system_admin("settings-admin5@example.com")
        admin_token = self._login(client, "settings-admin5@example.com")
        citizen_token = self._register_and_login_citizen(client, "settings-citizen2@example.com")

        try:
            enable_response = client.put(
                "/api/v1/admin/settings",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"maintenance_mode": True},
            )
            assert enable_response.status_code == 200

            citizen_login = client.post(
                "/api/v1/auth/login",
                json={"email": "settings-citizen2@example.com", "password": "Password123!"},
            )
            assert citizen_login.status_code == 401
            assert "maintenance" in citizen_login.get_json()["message"].lower()

            admin_login = client.post(
                "/api/v1/auth/login",
                json={"email": "settings-admin5@example.com", "password": "Admin@123456"},
            )
            assert admin_login.status_code == 200
        finally:
            self._reset_settings(client, admin_token)
            assert citizen_token  # token obtained before maintenance mode was enabled

    def test_disabling_notifications_prevents_new_notifications(self, app, client):
        self._ensure_system_admin("settings-admin6@example.com")
        admin_token = self._login(client, "settings-admin6@example.com")

        citizen_token = self._register_and_login_citizen(client, "settings-citizen3@example.com")
        citizen_id = None
        with app.app_context():
            citizen = User.query.filter_by(email="settings-citizen3@example.com").first()
            citizen_id = citizen.id

        complaint_response = client.post(
            "/api/v1/citizen/complaints",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={
                "title": "Pothole near settings test area",
                "description": "Testing notification gating behavior end to end.",
                "category": "pothole",
                "priority": "medium",
                "pincode": "226001",
                "image_url": "/api/v1/citizen/complaints/media/test-photo.jpg",
            },
        )
        assert complaint_response.status_code == 201
        complaint_id = complaint_response.get_json()["data"]["complaint"]["id"]

        try:
            disable_response = client.put(
                "/api/v1/admin/settings",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"notify_on_status_change": False},
            )
            assert disable_response.status_code == 200

            before_notifs = client.get(
                "/api/v1/notifications/", headers={"Authorization": f"Bearer {citizen_token}"}
            ).get_json()["data"]["items"]
            before_count = len(before_notifs)

            reject_response = client.put(
                f"/api/v1/admin/complaints/{complaint_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "status": "rejected",
                    "rejection_reason": "This report does not meet the submission criteria.",
                },
            )
            assert reject_response.status_code == 200

            after_notifs = client.get(
                "/api/v1/notifications/", headers={"Authorization": f"Bearer {citizen_token}"}
            ).get_json()["data"]["items"]
            assert len(after_notifs) == before_count
        finally:
            self._reset_settings(client, admin_token)
            assert citizen_id is not None
