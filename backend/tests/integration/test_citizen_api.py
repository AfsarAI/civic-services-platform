"""
Integration tests for Citizen API endpoints.
"""

import pytest


class TestCitizenEndpoints:
    """Integration tests for /api/v1/citizen endpoints."""

    def test_complaints_list_endpoint_exists(self, client):
        """Complaints list endpoint should exist."""
        response = client.get("/api/v1/citizen/complaints")
        assert response.status_code in (200, 401, 501)

    def test_dashboard_endpoint_exists(self, client):
        """Dashboard endpoint should exist."""
        response = client.get("/api/v1/citizen/dashboard")
        assert response.status_code in (200, 401, 501)
