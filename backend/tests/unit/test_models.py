"""
Unit tests for SQLAlchemy models.
"""

import pytest
from app.models.administrator_profile import AdministratorProfile
from app.models.city import City
from app.models.role import Role
from app.models.user import User
from app.models.complaint import Complaint


class TestRoleModel:
    """Unit tests for the Role model."""

    def test_role_constants_defined(self):
        assert Role.CITIZEN == "citizen"
        assert Role.ADMINISTRATOR == "administrator"
        assert Role.FIELD_WORKER == "field_worker"

    def test_role_repr(self, app):
        with app.app_context():
            role = Role(name="citizen", description="A citizen user")
            assert "citizen" in repr(role)


class TestUserModel:
    """Unit tests for the User model."""

    def test_password_hashing(self, app):
        with app.app_context():
            user = User(
                username="testuser",
                email="test@example.com",
                first_name="Test",
                last_name="User",
                role_id=1,
            )
            user.set_password("SecurePass123")
            assert user.password_hash != "SecurePass123"
            assert user.check_password("SecurePass123") is True
            assert user.check_password("WrongPassword") is False

    def test_full_name_property(self, app):
        with app.app_context():
            user = User(first_name="Jane", last_name="Doe", role_id=1)
            assert user.full_name == "Jane Doe"

    def test_admin_profile_properties(self, app):
        with app.app_context():
            city = City(name="Lucknow")
            profile = AdministratorProfile(
                admin_level=AdministratorProfile.MUNICIPAL,
                city=city,
            )
            user = User(first_name="Jane", last_name="Doe", role_id=1)
            user.role = Role(name=Role.ADMINISTRATOR)
            user.admin_profile = profile

            assert user.is_administrator is True
            assert user.is_municipal_admin is True
            assert user.admin_city_name == "Lucknow"


class TestComplaintModel:
    """Unit tests for the Complaint model."""

    def test_status_constants_defined(self):
        assert Complaint.STATUS_PENDING == "pending"
        assert Complaint.STATUS_RESOLVED == "resolved"

    def test_valid_statuses_list(self):
        assert "pending" in Complaint.VALID_STATUSES
        assert "resolved" in Complaint.VALID_STATUSES
        assert len(Complaint.VALID_STATUSES) == 6
