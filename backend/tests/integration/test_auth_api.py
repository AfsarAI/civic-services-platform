"""
Integration tests for the authentication API endpoints.
"""

from app.extensions import db
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
                "password": "Password123",
                "first_name": "New",
                "last_name": "Citizen",
            },
        )

        register_payload = register_response.get_json()
        assert register_response.status_code == 201
        assert register_payload["success"] is True
        assert register_payload["data"]["user"]["role"] == Role.CITIZEN

        login_response = self._login(client, "newcitizen@example.com", "Password123")
        login_payload = login_response.get_json()
        assert login_response.status_code == 200
        assert login_payload["success"] is True
        assert login_payload["data"]["user"]["email"] == "newcitizen@example.com"
