"""
Unit tests for administrator service municipal-admin flows.
"""

from datetime import datetime, timedelta, timezone

from app.api.administrator.service import AdminService
from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.audit_log import AuditLog
from app.models.city import City
from app.models.complaint import Complaint
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
                    "pincode": "226001",
                },
            )

            created_user = result["user"]
            audit_log = AuditLog.query.filter_by(
                action="municipal_admin_created",
                resource_id=created_user["id"],
            ).first()

            assert created_user["admin_level"] == AdministratorProfile.MUNICIPAL
            assert created_user["city_name"]
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
                "pincode": "226001",
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


class TestAdminServiceDashboardSummary:
    """Unit tests for AdminService.get_dashboard_summary (TPS-95)."""

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
    def _create_citizen(email: str, city_id: int = None) -> User:
        role = Role.query.filter_by(name=Role.CITIZEN).first()
        user = User(
            username=email.split("@")[0],
            email=email,
            first_name="Citizen",
            last_name="Tester",
            role_id=role.id,
            city_id=city_id,
            is_active=True,
        )
        user.set_password("Password123!")
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def _create_field_worker(email: str, city_id: int, is_active: bool = True) -> User:
        role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
        worker = User(
            username=email.split("@")[0],
            email=email,
            first_name="Field",
            last_name="Worker",
            role_id=role.id,
            city_id=city_id,
            is_active=is_active,
        )
        worker.set_password("Password123!")
        db.session.add(worker)
        db.session.commit()
        return worker

    @staticmethod
    def _create_complaint(
        citizen_id: int,
        city_id: int = None,
        priority: str = "medium",
        status: str = Complaint.STATUS_PENDING,
        created_at: datetime = None,
        resolved_at: datetime = None,
    ) -> Complaint:
        complaint = Complaint(
            citizen_id=citizen_id,
            title="Dashboard test complaint",
            description="Created directly for dashboard summary unit tests.",
            category=Complaint.CATEGORY_POTHOLE,
            priority=priority,
            status=status,
            city_id=city_id,
        )
        db.session.add(complaint)
        db.session.flush()
        if created_at is not None:
            complaint.created_at = created_at
        if resolved_at is not None:
            complaint.resolved_at = resolved_at
        db.session.commit()
        return complaint

    def test_system_scope_counts_only_open_high_priority_complaints(self, app):
        """Resolved high-priority complaints don't count — only open ones do."""
        with app.app_context():
            service = AdminService()
            admin = self._ensure_admin("dash-sys-hp-admin@example.com", AdministratorProfile.SYSTEM)
            citizen = self._create_citizen("dash-sys-hp-citizen@example.com")

            before = service.get_dashboard_summary(admin)["high_priority_complaints"]

            self._create_complaint(citizen.id, priority="high", status=Complaint.STATUS_PENDING)
            self._create_complaint(citizen.id, priority="high", status=Complaint.STATUS_RESOLVED)
            self._create_complaint(citizen.id, priority="medium", status=Complaint.STATUS_PENDING)

            after = service.get_dashboard_summary(admin)["high_priority_complaints"]
            assert after - before == 1

    def test_system_scope_computes_average_resolution_hours(self, app):
        with app.app_context():
            service = AdminService()
            admin = self._ensure_admin("dash-sys-avg-admin@example.com", AdministratorProfile.SYSTEM)
            citizen = self._create_citizen("dash-sys-avg-citizen@example.com")

            created_at = datetime.now(timezone.utc) - timedelta(hours=10)
            resolved_at = created_at + timedelta(hours=4)
            self._create_complaint(
                citizen.id,
                status=Complaint.STATUS_RESOLVED,
                created_at=created_at,
                resolved_at=resolved_at,
            )

            summary = service.get_dashboard_summary(admin)
            assert isinstance(summary["avg_resolution_hours"], float)

    def test_system_scope_active_field_workers_counts_unscoped_by_city(self, app):
        with app.app_context():
            service = AdminService()
            admin = self._ensure_admin("dash-sys-fw-admin@example.com", AdministratorProfile.SYSTEM)
            city = City(name="DashSysFWCity", is_active=True)
            db.session.add(city)
            db.session.commit()

            before = service.get_dashboard_summary(admin)["active_field_workers"]

            self._create_field_worker("dash-sys-fw-active@example.com", city.id, is_active=True)
            self._create_field_worker("dash-sys-fw-inactive@example.com", city.id, is_active=False)

            after = service.get_dashboard_summary(admin)["active_field_workers"]
            assert after - before == 1

    def test_municipal_scope_metrics_are_scoped_to_the_administrators_city(self, app):
        with app.app_context():
            service = AdminService()
            city_a = City(name="DashMuniCityA", is_active=True)
            city_b = City(name="DashMuniCityB", is_active=True)
            db.session.add_all([city_a, city_b])
            db.session.flush()

            admin_a = self._ensure_admin(
                "dash-muni-a-admin@example.com", AdministratorProfile.MUNICIPAL, "DashMuniCityA"
            )
            citizen_a = self._create_citizen("dash-muni-a-citizen@example.com", city_a.id)
            citizen_b = self._create_citizen("dash-muni-b-citizen@example.com", city_b.id)

            # In scope: high priority, open, filed in city A.
            self._create_complaint(
                citizen_a.id, city_id=city_a.id, priority="high", status=Complaint.STATUS_ASSIGNED
            )
            # Out of scope: high priority, open, but filed in city B.
            self._create_complaint(
                citizen_b.id, city_id=city_b.id, priority="high", status=Complaint.STATUS_ASSIGNED
            )

            self._create_field_worker("dash-muni-a-fw@example.com", city_a.id, is_active=True)
            self._create_field_worker("dash-muni-b-fw@example.com", city_b.id, is_active=True)

            summary = service.get_dashboard_summary(admin_a)
            assert summary["scope"] == "municipal"
            assert summary["high_priority_complaints"] == 1
            assert summary["active_field_workers"] == 1

    def test_municipal_scope_computes_average_resolution_hours_for_its_city(self, app):
        with app.app_context():
            service = AdminService()
            city = City(name="DashMuniAvgCity", is_active=True)
            db.session.add(city)
            db.session.flush()

            admin = self._ensure_admin(
                "dash-muni-avg-admin@example.com", AdministratorProfile.MUNICIPAL, "DashMuniAvgCity"
            )
            citizen = self._create_citizen("dash-muni-avg-citizen@example.com", city.id)

            created_at = datetime.now(timezone.utc) - timedelta(hours=8)
            resolved_at = created_at + timedelta(hours=2)
            self._create_complaint(
                citizen.id,
                city_id=city.id,
                status=Complaint.STATUS_RESOLVED,
                created_at=created_at,
                resolved_at=resolved_at,
            )

            summary = service.get_dashboard_summary(admin)
            assert summary["avg_resolution_hours"] == 2.0

    def test_municipal_scope_avg_resolution_hours_is_none_without_resolved_complaints(self, app):
        with app.app_context():
            service = AdminService()
            city = City(name="DashMuniEmptyCity", is_active=True)
            db.session.add(city)
            db.session.flush()

            admin = self._ensure_admin(
                "dash-muni-empty-admin@example.com", AdministratorProfile.MUNICIPAL, "DashMuniEmptyCity"
            )

            summary = service.get_dashboard_summary(admin)
            assert summary["avg_resolution_hours"] is None
            assert summary["high_priority_complaints"] == 0
