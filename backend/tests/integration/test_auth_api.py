"""
Integration tests for the authentication API endpoints.
"""

from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.city import City
from app.models.role import Role
from app.models.user import User


class TestAuthEndpoints:
    """Integration tests for /api/v1/auth endpoints."""

    @staticmethod
    def _ensure_user(email: str, role_name: str, password: str = "Admin@123456") -> User:
        role = Role.query.filter_by(name=role_name).first()
        assert role is not None

        user = User.query.filter_by(email=email).first()
        if user:
            return user

        user = User(
            username=email.split("@")[0],
            email=email,
            first_name="Test",
            last_name="User",
            role_id=role.id,
            is_active=True,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        if role_name == Role.ADMINISTRATOR:
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
    def _ensure_municipal_admin(email: str, city_name: str = "Lucknow") -> User:
        city = City.query.filter_by(name=city_name).first()
        if not city:
            city = City(name=city_name, is_active=True)
            db.session.add(city)
            db.session.flush()

        role = Role.query.filter_by(name=Role.ADMINISTRATOR).first()
        user = User.query.filter_by(email=email).first()
        if user:
            return user

        user = User(
            username=email.split("@")[0],
            email=email,
            first_name="Municipal",
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
                admin_level=AdministratorProfile.MUNICIPAL,
                city_id=city.id,
                created_by_id=None,
            )
        )
        db.session.commit()
        return user

    @staticmethod
    def _login(client, email: str, password: str):
        return client.post("/api/v1/auth/login", json={"email": email, "password": password})

    def test_swagger_docs_accessible(self, client):
        """Swagger UI should be reachable."""
        response = client.get("/api/v1/docs")
        assert response.status_code in (200, 308, 301)

    def test_admin_login_with_valid_credentials_returns_tokens_and_user(self, app, client):
        with app.app_context():
            self._ensure_user("admin@civicservices.local", Role.ADMINISTRATOR)

        response = self._login(client, "admin@civicservices.local", "Admin@123456")
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        assert payload["data"]["access_token"]
        assert payload["data"]["refresh_token"]
        assert payload["data"]["user"]["role"] == Role.ADMINISTRATOR
        assert payload["data"]["user"]["admin_level"] == AdministratorProfile.SYSTEM

    def test_invalid_credentials_return_unauthorised(self, app, client):
        with app.app_context():
            self._ensure_user("admin2@civicservices.local", Role.ADMINISTRATOR)

        response = self._login(client, "admin2@civicservices.local", "WrongPassword")
        payload = response.get_json()

        assert response.status_code == 401
        assert payload["success"] is False
        assert "invalid email or password" in payload["message"].lower()

    def test_admin_token_can_access_admin_dashboard(self, app, client):
        with app.app_context():
            self._ensure_user("admin3@civicservices.local", Role.ADMINISTRATOR)

        login_response = self._login(client, "admin3@civicservices.local", "Admin@123456")
        access_token = login_response.get_json()["data"]["access_token"]
        response = client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        assert "total_complaints" in payload["data"]

    def test_non_admin_token_cannot_access_admin_dashboard(self, app, client):
        with app.app_context():
            self._ensure_user("citizen@civicservices.local", Role.CITIZEN, password="Citizen@123")

        login_response = self._login(client, "citizen@civicservices.local", "Citizen@123")
        access_token = login_response.get_json()["data"]["access_token"]
        response = client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        payload = response.get_json()

        assert response.status_code == 403
        assert payload["success"] is False
        assert "administrator access required" in payload["message"].lower()

    def test_register_then_login_flow(self, client):
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newcitizen",
                "email": "newcitizen@example.com",
                "password": "Password123!",
                "first_name": "New",
                "last_name": "Citizen",
            },
        )

        register_payload = register_response.get_json()
        assert register_response.status_code == 201
        assert register_payload["success"] is True
        assert register_payload["data"]["user"]["role"] == Role.CITIZEN

        login_response = self._login(client, "newcitizen@example.com", "Password123!")
        login_payload = login_response.get_json()
        assert login_response.status_code == 200
        assert login_payload["success"] is True
        assert login_payload["data"]["user"]["email"] == "newcitizen@example.com"

    def test_municipal_admin_login_includes_city_and_admin_level(self, app, client):
        with app.app_context():
            self._ensure_municipal_admin("municipal@civicservices.local", city_name="Lucknow")

        response = self._login(client, "municipal@civicservices.local", "Admin@123456")
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["data"]["user"]["role"] == Role.ADMINISTRATOR
        assert payload["data"]["user"]["admin_level"] == AdministratorProfile.MUNICIPAL
        assert payload["data"]["user"]["city_name"] == "Lucknow"

    # ── Registration validation tests ─────────────────────────────────────

    def test_register_duplicate_email_returns_409(self, client):
        """Registering twice with the same email must return 409 Conflict."""
        payload = {
            "username": "dupuser1",
            "email": "duplicate@example.com",
            "password": "Secure@123",
            "first_name": "Dup",
            "last_name": "User",
        }
        r1 = client.post("/api/v1/auth/register", json=payload)
        assert r1.status_code == 201

        payload["username"] = "dupuser2"  # different username, same email
        r2 = client.post("/api/v1/auth/register", json=payload)
        assert r2.status_code == 409
        assert r2.get_json()["success"] is False
        assert "email" in r2.get_json()["message"].lower()

    def test_register_weak_password_returns_422(self, client):
        """Password with no uppercase/digit/special char must be rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "weakpwduser",
                "email": "weakpwd@example.com",
                "password": "onlylowercase",   # no uppercase, digit, or special char
                "first_name": "Weak",
                "last_name": "Pwd",
            },
        )
        assert response.status_code == 422
        assert response.get_json()["success"] is False

    def test_register_invalid_phone_returns_422(self, client):
        """Phone number with invalid format must be rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "phonetestuser",
                "email": "phonetest@example.com",
                "password": "Secure@123",
                "first_name": "Phone",
                "last_name": "Test",
                "phone": "abc-not-a-phone",
            },
        )
        assert response.status_code == 422
        payload = response.get_json()
        assert payload["success"] is False
        assert "phone" in str(payload["errors"]).lower()

    def test_register_valid_phone_is_accepted(self, client):
        """Valid Indian phone number must pass validation."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "validphoneuser",
                "email": "validphone@example.com",
                "password": "Secure@123",
                "first_name": "Valid",
                "last_name": "Phone",
                "phone": "+91-9876543210",
            },
        )
        assert response.status_code == 201

    def test_register_missing_required_fields_returns_422(self, client):
        """Missing/empty required fields must return 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "incomplete",
                "email": "",
                "password": "",
                "first_name": "",
                "last_name": "",
            },
        )
        assert response.status_code == 422
        errors = response.get_json()["errors"]
        assert "email" in errors
        assert "password" in errors
        assert "first_name" in errors
        assert "last_name" in errors

    def test_register_blank_first_name_returns_422(self, client):
        """Blank (whitespace-only) first name must be rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "blankname",
                "email": "blankname@example.com",
                "password": "Secure@123",
                "first_name": "   ",
                "last_name": "User",
            },
        )
        assert response.status_code == 422

    def test_login_inactive_account_returns_401(self, app, client):
        """Login attempt on a deactivated account must return 401."""
        with app.app_context():
            role = Role.query.filter_by(name=Role.CITIZEN).first()
            inactive_user = User.query.filter_by(email="inactive@example.com").first()
            if not inactive_user:
                inactive_user = User(
                    username="inactiveuser",
                    email="inactive@example.com",
                    first_name="Inactive",
                    last_name="User",
                    role_id=role.id,
                    is_active=False,
                )
                inactive_user.set_password("Secure@123")
                db.session.add(inactive_user)
                db.session.commit()

        response = self._login(client, "inactive@example.com", "Secure@123")
        assert response.status_code == 401
        assert "deactivated" in response.get_json()["message"].lower()

    def test_me_endpoint_returns_current_user(self, client):
        """Authenticated /auth/me must return the logged-in user's profile."""
        # Register + login fresh user
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "meuser",
                "email": "meuser@example.com",
                "password": "Secure@123",
                "first_name": "Me",
                "last_name": "User",
            },
        )
        login_resp = self._login(client, "meuser@example.com", "Secure@123")
        token = login_resp.get_json()["data"]["access_token"]

        me_resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        me_payload = me_resp.get_json()
        assert me_resp.status_code == 200
        assert me_payload["data"]["user"]["email"] == "meuser@example.com"
        assert me_payload["data"]["user"]["role"] == Role.CITIZEN
