"""
Integration tests for administrator hierarchy endpoints.
"""

from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.city import City
from app.models.role import Role
from app.models.user import User


class TestAdminHierarchyEndpoints:
    """Integration tests for system and municipal administrator permissions."""

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
        return response.get_json()["data"]["access_token"]

    def test_system_admin_can_create_municipal_administrator(self, app, client):
        with app.app_context():
            self._ensure_admin("sysadmin@civicservices.local", AdministratorProfile.SYSTEM)

        token = self._login(client, "sysadmin@civicservices.local")
        response = client.post(
            "/api/v1/admin/municipal-administrators",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "lucknow_admin",
                "email": "lucknow@civicservices.local",
                "password": "Municipal@123",
                "confirm_password": "Municipal@123",
                "first_name": "Lucknow",
                "last_name": "Admin",
                "pincode": "226001",
                "city_state": "Uttar Pradesh",
            },
        )
        payload = response.get_json()

        assert response.status_code == 201
        assert payload["success"] is True
        assert payload["data"]["user"]["admin_level"] == AdministratorProfile.MUNICIPAL
        assert payload["data"]["user"]["city_name"] == "Lucknow"

    def test_municipal_admin_user_list_scoped_to_own_city_citizens(self, app, client):
        with app.app_context():
            admin = self._ensure_admin(
                "municipal2@civicservices.local",
                AdministratorProfile.MUNICIPAL,
                city_name="Delhi",
            )
            other_city = City.query.filter_by(name="Mumbai").first()
            if not other_city:
                other_city = City(name="Mumbai", is_active=True)
                db.session.add(other_city)
                db.session.flush()

            citizen_role = Role.query.filter_by(name=Role.CITIZEN).first()
            own_city_citizen = User.query.filter_by(email="delhi-citizen@example.com").first()
            if not own_city_citizen:
                own_city_citizen = User(
                    username="delhicitizen",
                    email="delhi-citizen@example.com",
                    first_name="Delhi",
                    last_name="Citizen",
                    role_id=citizen_role.id,
                    city_id=admin.admin_city_id,
                    is_active=True,
                )
                own_city_citizen.set_password("Citizen@123")
                db.session.add(own_city_citizen)

            other_city_citizen = User.query.filter_by(email="mumbai-citizen@example.com").first()
            if not other_city_citizen:
                other_city_citizen = User(
                    username="mumbaicitizen",
                    email="mumbai-citizen@example.com",
                    first_name="Mumbai",
                    last_name="Citizen",
                    role_id=citizen_role.id,
                    city_id=other_city.id,
                    is_active=True,
                )
                other_city_citizen.set_password("Citizen@123")
                db.session.add(other_city_citizen)
            db.session.commit()

        token = self._login(client, "municipal2@civicservices.local")
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        payload = response.get_json()
        emails = [item["email"] for item in payload["data"]["items"]]
        assert "delhi-citizen@example.com" in emails
        assert "mumbai-citizen@example.com" not in emails
        assert all(item["role"] == "citizen" for item in payload["data"]["items"])

    def test_citizen_cannot_create_municipal_administrator(self, app, client):
        with app.app_context():
            role = Role.query.filter_by(name=Role.CITIZEN).first()
            citizen = User.query.filter_by(email="citizen-create-test@example.com").first()
            if not citizen:
                citizen = User(
                    username="citizencreatetest",
                    email="citizen-create-test@example.com",
                    first_name="Citizen",
                    last_name="Tester",
                    role_id=role.id,
                    is_active=True,
                )
                citizen.set_password("Citizen@123")
                db.session.add(citizen)
                db.session.commit()

        token = self._login(client, "citizen-create-test@example.com", "Citizen@123")
        response = client.post(
            "/api/v1/admin/municipal-administrators",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "citizen_blocked_admin",
                "email": "blocked.admin@example.com",
                "password": "Municipal@123",
                "confirm_password": "Municipal@123",
                "first_name": "Blocked",
                "last_name": "Admin",
                "pincode": "226001",
            },
        )

        assert response.status_code == 403
        assert "administrator access required" in response.get_json()["message"].lower()

    def test_anonymous_user_cannot_create_municipal_administrator(self, client):
        response = client.post(
            "/api/v1/admin/municipal-administrators",
            json={
                "username": "anonymous_admin",
                "email": "anonymous.admin@example.com",
                "password": "Municipal@123",
                "confirm_password": "Municipal@123",
                "first_name": "Anonymous",
                "last_name": "Admin",
                "pincode": "226001",
            },
        )

        assert response.status_code == 401

    def test_duplicate_municipal_admin_email_returns_409(self, app, client):
        with app.app_context():
            self._ensure_admin("sysadmin-dup@civicservices.local", AdministratorProfile.SYSTEM)

        token = self._login(client, "sysadmin-dup@civicservices.local")
        payload = {
            "username": "pune_admin_1",
            "email": "pune.admin@example.com",
            "password": "Municipal@123",
            "confirm_password": "Municipal@123",
            "first_name": "Pune",
            "last_name": "Admin",
            "pincode": "226001",
        }

        first = client.post(
            "/api/v1/admin/municipal-administrators",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        second = client.post(
            "/api/v1/admin/municipal-administrators",
            headers={"Authorization": f"Bearer {token}"},
            json={**payload, "username": "pune_admin_2"},
        )

        assert first.status_code == 201
        assert second.status_code == 409
        assert "email" in second.get_json()["message"].lower()

    def test_invalid_municipal_admin_payload_returns_422(self, app, client):
        with app.app_context():
            self._ensure_admin("sysadmin-invalid@civicservices.local", AdministratorProfile.SYSTEM)

        token = self._login(client, "sysadmin-invalid@civicservices.local")
        response = client.post(
            "/api/v1/admin/municipal-administrators",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "indore_admin",
                "email": "indore.admin@example.com",
                "password": "weakpassword",
                "confirm_password": "does-not-match",
                "first_name": "Indore",
                "last_name": "Admin",
                "phone": "abc",
                "pincode": "226001",
            },
        )

        payload = response.get_json()
        assert response.status_code == 422
        assert payload["success"] is False
        assert "password" in payload["errors"] or "confirm_password" in payload["errors"]

    def test_system_admin_can_deactivate_municipal_administrator(self, app, client):
        with app.app_context():
            self._ensure_admin("sysadmin-delete@civicservices.local", AdministratorProfile.SYSTEM)
            self._ensure_admin(
                "municipal-delete@civicservices.local",
                AdministratorProfile.MUNICIPAL,
                city_name="Surat",
            )
            municipal_user = User.query.filter_by(email="municipal-delete@civicservices.local").first()

        token = self._login(client, "sysadmin-delete@civicservices.local")
        response = client.delete(
            f"/api/v1/admin/municipal-administrators/{municipal_user.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.get_json()["data"]["user"]["is_active"] is False

    def test_system_admin_can_list_cities(self, app, client):
        with app.app_context():
            self._ensure_admin("sysadmin2@civicservices.local", AdministratorProfile.SYSTEM)
            if not City.query.filter_by(name="Mumbai").first():
                db.session.add(City(name="Mumbai", is_active=True))
                db.session.commit()

        token = self._login(client, "sysadmin2@civicservices.local")
        response = client.get(
            "/api/v1/admin/cities",
            headers={"Authorization": f"Bearer {token}"},
        )
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        assert any(city["name"] == "Mumbai" for city in payload["data"]["cities"])

    def test_system_admin_can_list_all_users(self, app, client):
        with app.app_context():
            self._ensure_admin("sysadmin-users-list@civicservices.local", AdministratorProfile.SYSTEM)

        token = self._login(client, "sysadmin-users-list@civicservices.local")
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        assert payload["data"]["pagination"]["total"] >= 1
        assert any(
            u["email"] == "sysadmin-users-list@civicservices.local"
            for u in payload["data"]["items"]
        )

    def test_system_admin_can_update_a_user(self, app, client):
        with app.app_context():
            self._ensure_admin("sysadmin-user-update@civicservices.local", AdministratorProfile.SYSTEM)
            role = Role.query.filter_by(name=Role.CITIZEN).first()
            target = User.query.filter_by(email="target-user@example.com").first()
            if not target:
                target = User(
                    username="targetuser",
                    email="target-user@example.com",
                    first_name="Target",
                    last_name="User",
                    role_id=role.id,
                    is_active=True,
                )
                target.set_password("Password123!")
                db.session.add(target)
                db.session.commit()
            target_id = target.id

        token = self._login(client, "sysadmin-user-update@civicservices.local")
        response = client.put(
            f"/api/v1/admin/users/{target_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"first_name": "Updated", "is_active": False},
        )
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["data"]["user"]["first_name"] == "Updated"
        assert payload["data"]["user"]["is_active"] is False

    def test_get_single_user_returns_404_when_missing(self, app, client):
        with app.app_context():
            self._ensure_admin("sysadmin-user-404@civicservices.local", AdministratorProfile.SYSTEM)

        token = self._login(client, "sysadmin-user-404@civicservices.local")
        response = client.get(
            "/api/v1/admin/users/999999",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
