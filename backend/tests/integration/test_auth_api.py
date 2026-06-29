"""
Integration tests for the authentication API endpoints.
"""

import pytest


class TestAuthEndpoints:
    """Integration tests for /api/v1/auth endpoints."""

    def test_swagger_docs_accessible(self, client):
        """Swagger UI should be reachable."""
        response = client.get("/api/v1/docs")
        assert response.status_code in (200, 308, 301)

    def test_login_endpoint_exists(self, client):
        """Login endpoint should exist (returns 501 until implemented)."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password"},
        )
        assert response.status_code in (200, 400, 401, 501)

    def test_register_endpoint_exists(self, client):
        """Register endpoint should exist."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "Password123",
                "first_name": "New",
                "last_name": "User",
            },
        )
        assert response.status_code in (201, 400, 409, 501)
