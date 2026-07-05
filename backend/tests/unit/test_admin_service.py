"""
Unit tests for administrator service municipal-admin flows.
"""

from app.api.administrator.service import AdminService
from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.audit_log import AuditLog
from app.models.role import Role
from app.models.user import User


class TestAdminServiceMunicipalAdministrators:
    """Unit tests for municipal-administrator management in AdminService."""

    @staticmethod
    def _ensure_system_admin() -> User:
        admin_role = Role.query.filter_by(name=Role.ADMINISTRATOR).first()
        user = User.query.filter_by(email="system-admin@example.com").first()
        if user:
            return user

        user = User(
            username="systemadmin",
            email="system-admin@example.com",
            first_name="System",
            last_name="Admin",
            role_id=admin_role.id,
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

    def test_create_municipal_administrator_creates_user_city_profile_and_audit_log(self, app):
        with app.app_context():
            service = AdminService()
            creator = self._ensure_system_admin()

            result = service.create_municipal_administrator(
                creator_id=creator.id,
                data={
                    "username": "kanpur_admin",
                    "email": "kanpur.admin@example.com",
                    "password": "Municipal@123",
                    "confirm_password": "Municipal@123",
                    "first_name": "Kanpur",
                    "last_name": "Administrator",
                    "phone": "+91-9876543210",
                    "city_name": "Kanpur",
                    "city_state": "Uttar Pradesh",
                },
            )

            created_user = result["user"]
            audit_log = AuditLog.query.filter_by(
                action="municipal_admin_created",
                resource_id=created_user["id"],
            ).first()

            assert created_user["admin_level"] == AdministratorProfile.MUNICIPAL
            assert created_user["city_name"] == "Kanpur"
            assert audit_log is not None

    def test_create_municipal_administrator_rejects_duplicate_email(self, app):
        with app.app_context():
            service = AdminService()
            creator = self._ensure_system_admin()
            payload = {
                "username": "bareilly_admin",
                "email": "bareilly.admin@example.com",
                "password": "Municipal@123",
                "confirm_password": "Municipal@123",
                "first_name": "Bareilly",
                "last_name": "Administrator",
                "city_name": "Bareilly",
            }

            service.create_municipal_administrator(creator.id, payload)

            try:
                service.create_municipal_administrator(
                    creator.id,
                    {**payload, "username": "bareilly_admin_2"},
                )
            except ValueError as exc:
                assert "email" in str(exc).lower()
            else:
                raise AssertionError("Expected duplicate email to raise ValueError")
