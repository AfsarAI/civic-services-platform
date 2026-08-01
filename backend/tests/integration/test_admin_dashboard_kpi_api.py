"""
Integration tests for the admin dashboard KPI metrics (TPS-97 Performance
Metrics Dashboard): verifies the full set of KPI fields is present on the
GET /api/v1/admin/dashboard response, date-range filtering, and invalid
date handling.
"""

from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.city import City
from app.models.role import Role
from app.models.user import User


class TestAdminDashboardKpiApi:
    """Integration tests for GET /api/v1/admin/dashboard KPI coverage."""

    @staticmethod
    def _ensure_city(name: str) -> City:
        city = City.query.filter_by(name=name).first()
        if not city:
            city = City(name=name, is_active=True)
            db.session.add(city)
            db.session.commit()
        return city

    @classmethod
    def _ensure_admin(cls, email: str, admin_level: str, city_name: str = None) -> User:
        role = Role.query.filter_by(name=Role.ADMINISTRATOR).first()
        user = User.query.filter_by(email=email).first()
        if user:
            return user

        city = cls._ensure_city(city_name) if city_name else None

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

    @classmethod
    def _submit_complaint(cls, client, citizen_token: str, city_id: int, priority: str = "high") -> int:
        response = client.post(
            "/api/v1/citizen/complaints",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={
                "title": "Deep pothole requiring urgent repair",
                "description": "Large pothole causing traffic issues near the junction.",
                "category": "pothole",
                "priority": priority,
                "city_id": city_id,
                "image_url": "/api/v1/citizen/complaints/media/test-photo.jpg",
            },
        )
        assert response.status_code == 201
        return response.get_json()["data"]["complaint"]["id"]

    REQUIRED_KPI_FIELDS = [
        "total_complaints",
        "open_complaints",
        "closed_complaints",
        "by_status",
        "avg_resolution_time_hours",
        "avg_assignment_time_hours",
        "complaint_closure_rate_percentage",
        "field_worker_completion_rate_percentage",
        "citizen_satisfaction_rating",
        "high_priority_pending_count",
    ]

    def test_system_admin_dashboard_includes_all_kpi_fields(self, app, client):
        self._ensure_admin("kpi-dash-sysadmin@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "kpi-dash-sysadmin@example.com")

        response = client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["scope"] == "system"

        for field in self.REQUIRED_KPI_FIELDS:
            assert field in data, f"Missing KPI field: {field}"

        assert isinstance(data["avg_resolution_time_hours"], (int, float))
        assert isinstance(data["avg_assignment_time_hours"], (int, float))
        assert isinstance(data["complaint_closure_rate_percentage"], (int, float))
        assert isinstance(data["field_worker_completion_rate_percentage"], (int, float))
        assert isinstance(data["citizen_satisfaction_rating"], (int, float))
        assert isinstance(data["high_priority_pending_count"], int)

    def test_municipal_admin_dashboard_includes_all_kpi_fields(self, app, client):
        self._ensure_admin("kpi-dash-muniadmin@example.com", AdministratorProfile.MUNICIPAL, "KpiDashCity")
        token = self._login(client, "kpi-dash-muniadmin@example.com")

        response = client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["scope"] == "municipal"

        for field in self.REQUIRED_KPI_FIELDS:
            assert field in data, f"Missing KPI field: {field}"

    def test_dashboard_high_priority_pending_count_reflects_urgent_open_complaints(self, app, client):
        self._ensure_admin("kpi-dash-sysadmin2@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "kpi-dash-sysadmin2@example.com")
        city = self._ensure_city("KpiDashCityB")
        citizen_auth = self._register_and_login_citizen(client, "kpi-dash-citizen-b@example.com")
        self._submit_complaint(client, citizen_auth["access_token"], city.id, priority="urgent")

        response = client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.get_json()["data"]["high_priority_pending_count"] >= 1

    def test_dashboard_date_range_filter_excludes_out_of_range_complaints(self, app, client):
        self._ensure_admin("kpi-dash-sysadmin3@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "kpi-dash-sysadmin3@example.com")
        city = self._ensure_city("KpiDashCityC")
        citizen_auth = self._register_and_login_citizen(client, "kpi-dash-citizen-c@example.com")
        self._submit_complaint(client, citizen_auth["access_token"], city.id)

        response = client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"},
            query_string={"date_from": "2999-01-01", "date_to": "2999-01-31"},
        )
        assert response.status_code == 200
        assert response.get_json()["data"]["total_complaints"] == 0

    def test_dashboard_invalid_date_from_returns_400(self, app, client):
        self._ensure_admin("kpi-dash-sysadmin4@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "kpi-dash-sysadmin4@example.com")

        response = client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"},
            query_string={"date_from": "not-a-date"},
        )
        assert response.status_code == 400
        assert response.get_json()["success"] is False

    def test_dashboard_invalid_date_to_returns_400(self, app, client):
        self._ensure_admin("kpi-dash-sysadmin5@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "kpi-dash-sysadmin5@example.com")

        response = client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"},
            query_string={"date_to": "31-12-2026"},
        )
        assert response.status_code == 400

    def test_non_admin_cannot_access_dashboard_kpis(self, app, client):
        citizen_auth = self._register_and_login_citizen(client, "kpi-dash-citizen-d@example.com")
        response = client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {citizen_auth['access_token']}"},
        )
        assert response.status_code == 403
