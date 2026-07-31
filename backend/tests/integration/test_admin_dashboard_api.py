"""
Integration tests for TPS-95: View Dashboard (GET /api/v1/admin/dashboard).
"""

from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.city import City
from app.models.role import Role
from app.models.user import User


class TestAdminDashboardApi:
    """Integration tests for the administrator dashboard endpoint."""

    @staticmethod
    def _ensure_admin(email: str, admin_level: str, city_name: str = None) -> User:
        role = Role.query.filter_by(name=Role.ADMINISTRATOR).first()
        user = User.query.filter_by(email=email).first()
        if user:
            return user

        city = None
        if city_name:
            city = City.query.filter_by(name=city_name).first()
            if not city:
                city = City(name=city_name, is_active=True)
                db.session.add(city)
                db.session.flush()

        user = User(
            username=email.split("@")[0],
            email=email,
            first_name="Admin",
            last_name=admin_level.title(),
            role_id=role.id,
            is_active=True,
        )
        user.set_password("Admin@123456")
        db.session.add(user)
        db.session.flush()
        db.session.add(
            AdministratorProfile(
                user_id=user.id,
                admin_level=admin_level,
                city_id=city.id if city else None,
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

    def test_system_admin_can_load_dashboard_with_new_kpi_fields(self, app, client):
        """AC1, AC2, AC5: system admin can access the dashboard and it returns
        the new TPS-95 KPI fields alongside the existing ones."""
        with app.app_context():
            self._ensure_admin("dash-api-sysadmin@example.com", AdministratorProfile.SYSTEM)

        token = self._login(client, "dash-api-sysadmin@example.com")
        response = client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        data = payload["data"]
        assert data["scope"] == "system"
        assert "high_priority_complaints" in data
        assert isinstance(data["high_priority_complaints"], int)
        assert "avg_resolution_hours" in data
        assert "active_field_workers" in data
        assert isinstance(data["active_field_workers"], int)
        # Pre-existing fields still present.
        assert "total_complaints" in data
        assert "by_status" in data
        assert "recent_complaints" in data

    def test_municipal_admin_can_load_dashboard_with_new_kpi_fields(self, app, client):
        """AC1, AC2, AC5: municipal admin gets the same new fields, city-scoped."""
        with app.app_context():
            self._ensure_admin(
                "dash-api-muniadmin@example.com", AdministratorProfile.MUNICIPAL, "DashApiCity"
            )

        token = self._login(client, "dash-api-muniadmin@example.com")
        response = client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
        payload = response.get_json()

        assert response.status_code == 200
        data = payload["data"]
        assert data["scope"] == "municipal"
        assert "high_priority_complaints" in data
        assert "avg_resolution_hours" in data
        assert "active_field_workers" in data
        assert "total_field_workers" in data
        assert data["managed_city"]["name"] == "DashApiCity"

    def test_non_admin_cannot_access_dashboard(self, client):
        """Access control: only administrators can reach this endpoint."""
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "dash_api_citizen",
                "email": "dash-api-citizen@example.com",
                "password": "Password123!",
                "first_name": "Citizen",
                "last_name": "Tester",
                "pincode": "226001",
            },
        )
        assert register_response.status_code == 201
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "dash-api-citizen@example.com", "password": "Password123!"},
        )
        token = login_response.get_json()["data"]["access_token"]

        response = client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    def test_dashboard_requires_authentication(self, client):
        response = client.get("/api/v1/admin/dashboard")
        assert response.status_code == 401
