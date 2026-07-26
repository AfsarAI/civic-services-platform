"""
Integration tests for city-scoped administrator behavior:
- Municipal administrators can create/edit/deactivate field workers in their
  own city only.
- Municipal administrators only see and can only act on complaints and field
  workers belonging to their own city.
- System administrators remain unscoped (see/act across all cities) but
  cannot create field workers directly.
"""

from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.city import City
from app.models.role import Role
from app.models.user import User


class TestAdminCityScoping:
    """Integration tests for city-based administrator scoping."""

    @staticmethod
    def _ensure_city(name: str) -> City:
        city = City.query.filter_by(name=name).first()
        if not city:
            city = City(name=name, is_active=True)
            db.session.add(city)
            db.session.flush()
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
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Password123!"},
        )
        assert login_response.status_code == 200
        return login_response.get_json()["data"]

    @classmethod
    def _submit_complaint(cls, client, citizen_token: str, city_id: int, title: str) -> int:
        response = client.post(
            "/api/v1/citizen/complaints",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={
                "title": title,
                "description": "Deep pothole requiring urgent repair work.",
                "category": "pothole",
                "priority": "high",
                "city_id": city_id,
                "image_url": "/api/v1/citizen/complaints/media/test-photo.jpg",
            },
        )
        assert response.status_code == 201
        return response.get_json()["data"]["complaint"]["id"]

    def _setup_two_cities(self, app, client, suffix: str):
        with app.app_context():
            lucknow = self._ensure_city("Lucknow")
            kanpur = self._ensure_city("Kanpur City")
            self._ensure_admin("lucknow-admin@example.com", AdministratorProfile.MUNICIPAL, "Lucknow")
            self._ensure_admin("kanpur-admin@example.com", AdministratorProfile.MUNICIPAL, "Kanpur City")
            self._ensure_admin("sysadmin-scope@example.com", AdministratorProfile.SYSTEM)
            lucknow_id, kanpur_id = lucknow.id, kanpur.id

        citizen_auth = self._register_and_login_citizen(client, f"scopecitizen-{suffix}@example.com")
        citizen_token = citizen_auth["access_token"]

        lucknow_complaint_id = self._submit_complaint(client, citizen_token, lucknow_id, "Pothole near Lucknow market")
        kanpur_complaint_id = self._submit_complaint(client, citizen_token, kanpur_id, "Pothole near Kanpur mall")

        return {
            "lucknow_id": lucknow_id,
            "kanpur_id": kanpur_id,
            "lucknow_complaint_id": lucknow_complaint_id,
            "kanpur_complaint_id": kanpur_complaint_id,
        }

    def test_municipal_admin_only_sees_own_city_complaints(self, app, client):
        ctx = self._setup_two_cities(app, client, "a")
        lucknow_token = self._login(client, "lucknow-admin@example.com")

        response = client.get(
            "/api/v1/admin/complaints",
            headers={"Authorization": f"Bearer {lucknow_token}"},
        )
        assert response.status_code == 200
        items = response.get_json()["data"]["items"]
        ids = {c["id"] for c in items}
        assert ctx["lucknow_complaint_id"] in ids
        assert ctx["kanpur_complaint_id"] not in ids

    def test_system_admin_sees_all_cities_complaints(self, app, client):
        ctx = self._setup_two_cities(app, client, "b")
        sys_token = self._login(client, "sysadmin-scope@example.com")

        response = client.get(
            "/api/v1/admin/complaints",
            headers={"Authorization": f"Bearer {sys_token}"},
        )
        assert response.status_code == 200
        ids = {c["id"] for c in response.get_json()["data"]["items"]}
        assert ctx["lucknow_complaint_id"] in ids
        assert ctx["kanpur_complaint_id"] in ids

    def test_municipal_admin_cannot_view_other_city_complaint(self, app, client):
        ctx = self._setup_two_cities(app, client, "c")
        lucknow_token = self._login(client, "lucknow-admin@example.com")

        response = client.get(
            f"/api/v1/admin/complaints/{ctx['kanpur_complaint_id']}",
            headers={"Authorization": f"Bearer {lucknow_token}"},
        )
        assert response.status_code == 404

    def test_municipal_admin_creates_field_worker_in_own_city(self, app, client):
        self._setup_two_cities(app, client, "d")
        lucknow_token = self._login(client, "lucknow-admin@example.com")

        response = client.post(
            "/api/v1/admin/field-workers",
            headers={"Authorization": f"Bearer {lucknow_token}"},
            json={
                "username": "lucknow_worker1",
                "email": "lucknow.worker1@example.com",
                "password": "Worker@123",
                "confirm_password": "Worker@123",
                "first_name": "Suresh",
                "last_name": "Yadav",
            },
        )
        payload = response.get_json()
        assert response.status_code == 201
        assert payload["data"]["user"]["role"] == "field_worker"
        assert payload["data"]["user"]["city_name"] == "Lucknow"
        assert payload["data"]["user"]["is_active"] is True

    def test_system_admin_cannot_create_field_worker(self, app, client):
        self._setup_two_cities(app, client, "e")
        sys_token = self._login(client, "sysadmin-scope@example.com")

        response = client.post(
            "/api/v1/admin/field-workers",
            headers={"Authorization": f"Bearer {sys_token}"},
            json={
                "username": "sys_created_worker",
                "email": "sys.worker@example.com",
                "password": "Worker@123",
                "confirm_password": "Worker@123",
                "first_name": "Sys",
                "last_name": "Worker",
            },
        )
        assert response.status_code == 403

    def test_municipal_admin_only_sees_own_city_field_workers(self, app, client):
        self._setup_two_cities(app, client, "f")
        lucknow_token = self._login(client, "lucknow-admin@example.com")
        kanpur_token = self._login(client, "kanpur-admin@example.com")

        client.post(
            "/api/v1/admin/field-workers",
            headers={"Authorization": f"Bearer {lucknow_token}"},
            json={
                "username": "lucknow_worker2",
                "email": "lucknow.worker2@example.com",
                "password": "Worker@123",
                "confirm_password": "Worker@123",
                "first_name": "Amit",
                "last_name": "Singh",
            },
        )
        client.post(
            "/api/v1/admin/field-workers",
            headers={"Authorization": f"Bearer {kanpur_token}"},
            json={
                "username": "kanpur_worker1",
                "email": "kanpur.worker1@example.com",
                "password": "Worker@123",
                "confirm_password": "Worker@123",
                "first_name": "Vikram",
                "last_name": "Rao",
            },
        )

        response = client.get(
            "/api/v1/admin/field-workers",
            headers={"Authorization": f"Bearer {lucknow_token}"},
        )
        emails = {w["email"] for w in response.get_json()["data"]["field_workers"]}
        assert "lucknow.worker2@example.com" in emails
        assert "kanpur.worker1@example.com" not in emails

    def test_municipal_admin_can_deactivate_and_edit_own_field_worker(self, app, client):
        self._setup_two_cities(app, client, "g")
        lucknow_token = self._login(client, "lucknow-admin@example.com")

        create_response = client.post(
            "/api/v1/admin/field-workers",
            headers={"Authorization": f"Bearer {lucknow_token}"},
            json={
                "username": "lucknow_worker3",
                "email": "lucknow.worker3@example.com",
                "password": "Worker@123",
                "confirm_password": "Worker@123",
                "first_name": "Deepak",
                "last_name": "Mehra",
            },
        )
        worker_id = create_response.get_json()["data"]["user"]["id"]

        update_response = client.put(
            f"/api/v1/admin/field-workers/{worker_id}",
            headers={"Authorization": f"Bearer {lucknow_token}"},
            json={"is_active": False, "phone": "+91-9876500000"},
        )
        assert update_response.status_code == 200
        updated = update_response.get_json()["data"]["user"]
        assert updated["is_active"] is False
        assert updated["phone"] == "+91-9876500000"

    def test_municipal_admin_cannot_manage_other_citys_field_worker(self, app, client):
        self._setup_two_cities(app, client, "h")
        lucknow_token = self._login(client, "lucknow-admin@example.com")
        kanpur_token = self._login(client, "kanpur-admin@example.com")

        create_response = client.post(
            "/api/v1/admin/field-workers",
            headers={"Authorization": f"Bearer {lucknow_token}"},
            json={
                "username": "lucknow_worker4",
                "email": "lucknow.worker4@example.com",
                "password": "Worker@123",
                "confirm_password": "Worker@123",
                "first_name": "Rohit",
                "last_name": "Sharma",
            },
        )
        worker_id = create_response.get_json()["data"]["user"]["id"]

        response = client.get(
            f"/api/v1/admin/field-workers/{worker_id}",
            headers={"Authorization": f"Bearer {kanpur_token}"},
        )
        assert response.status_code == 404

    def test_assign_complaint_requires_worker_in_same_city(self, app, client):
        ctx = self._setup_two_cities(app, client, "i")
        lucknow_token = self._login(client, "lucknow-admin@example.com")
        kanpur_token = self._login(client, "kanpur-admin@example.com")

        kanpur_worker_response = client.post(
            "/api/v1/admin/field-workers",
            headers={"Authorization": f"Bearer {kanpur_token}"},
            json={
                "username": "kanpur_worker2",
                "email": "kanpur.worker2@example.com",
                "password": "Worker@123",
                "confirm_password": "Worker@123",
                "first_name": "Manoj",
                "last_name": "Tiwari",
            },
        )
        kanpur_worker_id = kanpur_worker_response.get_json()["data"]["user"]["id"]

        response = client.post(
            f"/api/v1/admin/complaints/{ctx['lucknow_complaint_id']}/assign",
            headers={"Authorization": f"Bearer {lucknow_token}"},
            json={"worker_id": kanpur_worker_id},
        )
        assert response.status_code == 400
        assert "city" in response.get_json()["message"].lower()

    def test_assign_complaint_succeeds_with_same_city_worker(self, app, client):
        ctx = self._setup_two_cities(app, client, "j")
        lucknow_token = self._login(client, "lucknow-admin@example.com")

        worker_response = client.post(
            "/api/v1/admin/field-workers",
            headers={"Authorization": f"Bearer {lucknow_token}"},
            json={
                "username": "lucknow_worker5",
                "email": "lucknow.worker5@example.com",
                "password": "Worker@123",
                "confirm_password": "Worker@123",
                "first_name": "Sanjay",
                "last_name": "Gupta",
            },
        )
        worker_id = worker_response.get_json()["data"]["user"]["id"]

        response = client.post(
            f"/api/v1/admin/complaints/{ctx['lucknow_complaint_id']}/assign",
            headers={"Authorization": f"Bearer {lucknow_token}"},
            json={"worker_id": worker_id},
        )
        assert response.status_code == 201
        assert response.get_json()["data"]["complaint"]["status"] == "assigned"

    def test_municipal_admin_cannot_verify_other_city_repair(
        self, app, client
    ):
        ctx = self._setup_two_cities(app, client, "verify")
        lucknow_token = self._login(client, "lucknow-admin@example.com")
        kanpur_token = self._login(client, "kanpur-admin@example.com")

        worker_response = client.post(
            "/api/v1/admin/field-workers",
            headers={"Authorization": f"Bearer {kanpur_token}"},
            json={
                "username": "kanpur_verify_worker",
                "email": "kanpur.verify.worker@example.com",
                "password": "Worker@123",
                "confirm_password": "Worker@123",
                "first_name": "Verify",
                "last_name": "Worker",
            },
        )
        worker_id = worker_response.get_json()["data"]["user"]["id"]
        assignment_id = client.post(
            (
                "/api/v1/admin/complaints/"
                f"{ctx['kanpur_complaint_id']}/assign"
            ),
            headers={"Authorization": f"Bearer {kanpur_token}"},
            json={"worker_id": worker_id},
        ).get_json()["data"]["assignment"]["id"]
        worker_token = self._login(
            client,
            "kanpur.verify.worker@example.com",
            "Worker@123",
        )
        client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/accept",
            headers={"Authorization": f"Bearer {worker_token}"},
        )
        client.post(
            f"/api/v1/fieldworker/assignments/{assignment_id}/complete",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={},
        )

        for payload in (
            {"decision": "approved"},
            {
                "decision": "rework_requested",
                "remarks": "Redo this repair.",
            },
        ):
            response = client.post(
                (
                    "/api/v1/admin/complaints/"
                    f"{ctx['kanpur_complaint_id']}/verify"
                ),
                headers={"Authorization": f"Bearer {lucknow_token}"},
                json=payload,
            )
            assert response.status_code == 404

    def test_municipal_dashboard_reflects_city_scoped_data(self, app, client):
        ctx = self._setup_two_cities(app, client, "k")
        lucknow_token = self._login(client, "lucknow-admin@example.com")

        response = client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {lucknow_token}"},
        )
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["scope"] == "municipal"
        assert data["total_complaints"] >= 1
        recent_ids = {c["id"] for c in data["recent_complaints"]}
        assert ctx["lucknow_complaint_id"] in recent_ids
        assert ctx["kanpur_complaint_id"] not in recent_ids
