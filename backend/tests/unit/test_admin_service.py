"""
Unit tests for administrator service municipal-admin flows.
"""

from datetime import datetime, timedelta, timezone

import pytest
from app.api.administrator.service import AdminService, VerificationConflictError
from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.audit_log import AuditLog
from app.models.city import City
from app.models.complaint import Complaint
from app.models.complaint_assignment import ComplaintAssignment
from app.models.complaint_verification import ComplaintVerification
from app.models.role import Role
from app.models.user import User


def _mgmt_ensure_city(name: str) -> City:
    city = City.query.filter_by(name=name).first()
    if not city:
        city = City(name=name, is_active=True)
        db.session.add(city)
        db.session.commit()
    return city


def _mgmt_ensure_admin(email: str, admin_level: str, city_name: str = None) -> User:
    role = Role.query.filter_by(name=Role.ADMINISTRATOR).first()
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    city = _mgmt_ensure_city(city_name) if city_name else None
    user = User(
        username=email.split("@")[0], email=email, first_name="Admin",
        last_name=admin_level.title(), role_id=role.id, is_active=True,
        city_id=city.id if city else None,
    )
    user.set_password("Admin@123456")
    db.session.add(user)
    db.session.flush()
    db.session.add(AdministratorProfile(
        user_id=user.id, admin_level=admin_level,
        city_id=city.id if city else None, created_by_id=None,
    ))
    db.session.commit()
    return user


def _mgmt_ensure_citizen(email: str, city_id: int = None) -> User:
    role = Role.query.filter_by(name=Role.CITIZEN).first()
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(
        username=email.split("@")[0], email=email, first_name="Test",
        last_name="Citizen", role_id=role.id, city_id=city_id, is_active=True,
    )
    user.set_password("Citizen@123")
    db.session.add(user)
    db.session.commit()
    return user


def _mgmt_ensure_worker(email: str, city_id: int) -> User:
    role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(
        username=email.split("@")[0], email=email, first_name="Field",
        last_name="Worker", role_id=role.id, city_id=city_id, is_active=True,
    )
    user.set_password("Worker@123")
    db.session.add(user)
    db.session.commit()
    return user


def _mgmt_make_complaint(citizen_id, city_id=None, status=Complaint.STATUS_PENDING) -> Complaint:
    complaint = Complaint(
        citizen_id=citizen_id, title="Pothole for admin unit tests",
        description="A complaint used for administrator service unit tests.",
        category=Complaint.CATEGORY_POTHOLE, status=status, priority="medium",
        city_id=city_id,
    )
    db.session.add(complaint)
    db.session.commit()
    return complaint


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


class TestAdminServiceComplaints:
    """Unit tests for get_all_complaints, get_complaint, update_complaint,
    verify_repair, assign_complaint, and get_assignment_monitor."""

    def test_get_all_complaints_filters_by_city(self, app):
        with app.app_context():
            city_a = _mgmt_ensure_city("MgmtComplaintsCityA")
            city_b = _mgmt_ensure_city("MgmtComplaintsCityB")
            citizen = _mgmt_ensure_citizen("mgmt.complaints.citizen1@example.com")
            _mgmt_make_complaint(citizen.id, city_a.id)
            _mgmt_make_complaint(citizen.id, city_b.id)
            service = AdminService()
            result = service.get_all_complaints(city_id=city_a.id)
            assert all(item["city_id"] == city_a.id for item in result["items"])

    def test_get_all_complaints_rejects_invalid_status(self, app):
        with app.app_context():
            service = AdminService()
            with pytest.raises(ValueError, match="Invalid status"):
                service.get_all_complaints(status="not-a-status")

    def test_get_complaint_returns_full_details(self, app):
        with app.app_context():
            citizen = _mgmt_ensure_citizen("mgmt.complaints.citizen2@example.com")
            complaint = _mgmt_make_complaint(citizen.id)
            service = AdminService()
            result = service.get_complaint(complaint.id)
            assert result["complaint"]["id"] == complaint.id

    def test_get_complaint_scoped_out_of_city_raises(self, app):
        with app.app_context():
            city_a = _mgmt_ensure_city("MgmtComplaintsCityC")
            city_b = _mgmt_ensure_city("MgmtComplaintsCityD")
            citizen = _mgmt_ensure_citizen("mgmt.complaints.citizen3@example.com")
            complaint = _mgmt_make_complaint(citizen.id, city_a.id)
            service = AdminService()
            with pytest.raises(ValueError, match="not found"):
                service.get_complaint(complaint.id, city_id=city_b.id)

    def test_update_complaint_changes_priority_without_status(self, app):
        with app.app_context():
            citizen = _mgmt_ensure_citizen("mgmt.complaints.citizen4@example.com")
            complaint = _mgmt_make_complaint(citizen.id)
            service = AdminService()
            result = service.update_complaint(complaint.id, {"priority": "urgent"})
            assert result["complaint"]["priority"] == "urgent"
            assert result["complaint"]["status"] == Complaint.STATUS_PENDING

    def test_update_complaint_rejects_invalid_transition(self, app):
        with app.app_context():
            citizen = _mgmt_ensure_citizen("mgmt.complaints.citizen5@example.com")
            complaint = _mgmt_make_complaint(citizen.id, status=Complaint.STATUS_PENDING)
            service = AdminService()
            with pytest.raises(ValueError, match="Cannot move complaint"):
                service.update_complaint(complaint.id, {"status": Complaint.STATUS_CLOSED})

    def test_update_complaint_rejects_direct_resolve(self, app):
        with app.app_context():
            citizen = _mgmt_ensure_citizen("mgmt.complaints.citizen6@example.com")
            complaint = _mgmt_make_complaint(citizen.id, status=Complaint.STATUS_IN_PROGRESS)
            service = AdminService()
            with pytest.raises(ValueError, match="repair verification"):
                service.update_complaint(complaint.id, {"status": Complaint.STATUS_RESOLVED})

    def test_update_complaint_rejects_transitions_to_reject_from_closed(self, app):
        with app.app_context():
            citizen = _mgmt_ensure_citizen("mgmt.complaints.citizen6b@example.com")
            complaint = _mgmt_make_complaint(citizen.id, status=Complaint.STATUS_CLOSED)
            service = AdminService()
            with pytest.raises(ValueError, match="Cannot move complaint"):
                service.update_complaint(complaint.id, {"status": Complaint.STATUS_REJECTED})

    def test_assign_complaint_creates_assignment_and_updates_status(self, app):
        with app.app_context():
            city = _mgmt_ensure_city("MgmtAssignCity1")
            citizen = _mgmt_ensure_citizen("mgmt.assign.citizen1@example.com")
            admin = _mgmt_ensure_admin("mgmt.assign.admin1@example.com", AdministratorProfile.SYSTEM)
            worker = _mgmt_ensure_worker("mgmt.assign.worker1@example.com", city.id)
            complaint = _mgmt_make_complaint(citizen.id, city.id)
            service = AdminService()
            result = service.assign_complaint(complaint.id, admin.id, {"worker_id": worker.id})
            assert result["assignment"]["worker_id"] == worker.id
            assert result["complaint"]["status"] == Complaint.STATUS_ASSIGNED

    def test_assign_complaint_rejects_non_field_worker(self, app):
        with app.app_context():
            city = _mgmt_ensure_city("MgmtAssignCity2")
            citizen = _mgmt_ensure_citizen("mgmt.assign.citizen2@example.com")
            admin = _mgmt_ensure_admin("mgmt.assign.admin2@example.com", AdministratorProfile.SYSTEM)
            complaint = _mgmt_make_complaint(citizen.id, city.id)
            service = AdminService()
            with pytest.raises(ValueError, match="not a field worker"):
                service.assign_complaint(complaint.id, admin.id, {"worker_id": citizen.id})

    def test_assign_complaint_rejects_worker_from_different_city(self, app):
        with app.app_context():
            city_a = _mgmt_ensure_city("MgmtAssignCityA")
            city_b = _mgmt_ensure_city("MgmtAssignCityB")
            citizen = _mgmt_ensure_citizen("mgmt.assign.citizen3@example.com")
            admin = _mgmt_ensure_admin(
                "mgmt.assign.admin3@example.com", AdministratorProfile.MUNICIPAL, "MgmtAssignCityA"
            )
            worker = _mgmt_ensure_worker("mgmt.assign.worker2@example.com", city_b.id)
            complaint = _mgmt_make_complaint(citizen.id, city_a.id)
            service = AdminService()
            with pytest.raises(ValueError, match="does not belong to your city"):
                service.assign_complaint(complaint.id, admin.id, {"worker_id": worker.id}, city_id=city_a.id)

    def test_assign_complaint_rejects_already_resolved_complaint(self, app):
        with app.app_context():
            city = _mgmt_ensure_city("MgmtAssignCity3")
            citizen = _mgmt_ensure_citizen("mgmt.assign.citizen4@example.com")
            admin = _mgmt_ensure_admin("mgmt.assign.admin4@example.com", AdministratorProfile.SYSTEM)
            worker = _mgmt_ensure_worker("mgmt.assign.worker3@example.com", city.id)
            complaint = _mgmt_make_complaint(citizen.id, city.id, status=Complaint.STATUS_RESOLVED)
            service = AdminService()
            with pytest.raises(ValueError, match="Only pending or already-assigned"):
                service.assign_complaint(complaint.id, admin.id, {"worker_id": worker.id})

    def test_get_assignment_monitor_lists_assignments(self, app):
        with app.app_context():
            city = _mgmt_ensure_city("MgmtMonitorCity1")
            citizen = _mgmt_ensure_citizen("mgmt.monitor.citizen1@example.com")
            admin = _mgmt_ensure_admin("mgmt.monitor.admin1@example.com", AdministratorProfile.SYSTEM)
            worker = _mgmt_ensure_worker("mgmt.monitor.worker1@example.com", city.id)
            complaint = _mgmt_make_complaint(citizen.id, city.id)
            service = AdminService()
            service.assign_complaint(complaint.id, admin.id, {"worker_id": worker.id})
            result = service.get_assignment_monitor(city_id=city.id)
            assert result["total"] >= 1

    def test_get_assignment_monitor_rejects_invalid_status(self, app):
        with app.app_context():
            service = AdminService()
            with pytest.raises(ValueError, match="Invalid assignment status"):
                service.get_assignment_monitor(status="not-a-status")

    def test_verify_repair_approves_completed_repair(self, app):
        with app.app_context():
            city = _mgmt_ensure_city("MgmtVerifyCity1")
            citizen = _mgmt_ensure_citizen("mgmt.verify.citizen1@example.com")
            admin = _mgmt_ensure_admin("mgmt.verify.admin1@example.com", AdministratorProfile.SYSTEM)
            worker = _mgmt_ensure_worker("mgmt.verify.worker1@example.com", city.id)
            complaint = _mgmt_make_complaint(citizen.id, city.id, status=Complaint.STATUS_IN_PROGRESS)
            assignment = ComplaintAssignment(
                complaint_id=complaint.id, worker_id=worker.id, assigned_by_id=admin.id,
                status=ComplaintAssignment.STATUS_COMPLETED,
                completed_at=datetime.now(timezone.utc),
            )
            db.session.add(assignment)
            db.session.commit()

            service = AdminService()
            result = service.verify_repair(
                complaint.id, admin.id, {"decision": ComplaintVerification.DECISION_APPROVED}
            )
            assert result["complaint"]["status"] == Complaint.STATUS_RESOLVED

    def test_verify_repair_requests_rework_with_remarks(self, app):
        with app.app_context():
            city = _mgmt_ensure_city("MgmtVerifyCity2")
            citizen = _mgmt_ensure_citizen("mgmt.verify.citizen2@example.com")
            admin = _mgmt_ensure_admin("mgmt.verify.admin2@example.com", AdministratorProfile.SYSTEM)
            worker = _mgmt_ensure_worker("mgmt.verify.worker2@example.com", city.id)
            complaint = _mgmt_make_complaint(citizen.id, city.id, status=Complaint.STATUS_IN_PROGRESS)
            assignment = ComplaintAssignment(
                complaint_id=complaint.id, worker_id=worker.id, assigned_by_id=admin.id,
                status=ComplaintAssignment.STATUS_COMPLETED,
                completed_at=datetime.now(timezone.utc),
            )
            db.session.add(assignment)
            db.session.commit()

            service = AdminService()
            result = service.verify_repair(complaint.id, admin.id, {
                "decision": ComplaintVerification.DECISION_REWORK_REQUESTED,
                "remarks": "Please redo the edge finishing.",
            })
            assert result["complaint"]["status"] == Complaint.STATUS_IN_PROGRESS

    def test_verify_repair_requires_remarks_for_rework(self, app):
        with app.app_context():
            city = _mgmt_ensure_city("MgmtVerifyCity3")
            citizen = _mgmt_ensure_citizen("mgmt.verify.citizen3@example.com")
            admin = _mgmt_ensure_admin("mgmt.verify.admin3@example.com", AdministratorProfile.SYSTEM)
            worker = _mgmt_ensure_worker("mgmt.verify.worker3@example.com", city.id)
            complaint = _mgmt_make_complaint(citizen.id, city.id, status=Complaint.STATUS_IN_PROGRESS)
            assignment = ComplaintAssignment(
                complaint_id=complaint.id, worker_id=worker.id, assigned_by_id=admin.id,
                status=ComplaintAssignment.STATUS_COMPLETED,
                completed_at=datetime.now(timezone.utc),
            )
            db.session.add(assignment)
            db.session.commit()

            service = AdminService()
            with pytest.raises(ValueError, match="remarks are required"):
                service.verify_repair(
                    complaint.id, admin.id, {"decision": ComplaintVerification.DECISION_REWORK_REQUESTED}
                )

    def test_verify_repair_rejects_when_not_awaiting_verification(self, app):
        with app.app_context():
            citizen = _mgmt_ensure_citizen("mgmt.verify.citizen4@example.com")
            admin = _mgmt_ensure_admin("mgmt.verify.admin4@example.com", AdministratorProfile.SYSTEM)
            complaint = _mgmt_make_complaint(citizen.id, status=Complaint.STATUS_PENDING)
            service = AdminService()
            with pytest.raises(ValueError, match="awaiting verification"):
                service.verify_repair(
                    complaint.id, admin.id, {"decision": ComplaintVerification.DECISION_APPROVED}
                )

    def test_verify_repair_rejects_duplicate_verification(self, app):
        with app.app_context():
            city = _mgmt_ensure_city("MgmtVerifyCity5")
            citizen = _mgmt_ensure_citizen("mgmt.verify.citizen5@example.com")
            admin = _mgmt_ensure_admin("mgmt.verify.admin5@example.com", AdministratorProfile.SYSTEM)
            worker = _mgmt_ensure_worker("mgmt.verify.worker5@example.com", city.id)
            complaint = _mgmt_make_complaint(citizen.id, city.id, status=Complaint.STATUS_IN_PROGRESS)
            completed_at = datetime.now(timezone.utc)
            assignment = ComplaintAssignment(
                complaint_id=complaint.id, worker_id=worker.id, assigned_by_id=admin.id,
                status=ComplaintAssignment.STATUS_COMPLETED, completed_at=completed_at,
            )
            db.session.add(assignment)
            db.session.commit()

            service = AdminService()
            db.session.add(ComplaintVerification(
                complaint_id=complaint.id, assignment_id=assignment.id,
                administrator_id=admin.id, decision=ComplaintVerification.DECISION_APPROVED,
                repair_completed_at=completed_at,
            ))
            db.session.commit()
            # Reset the complaint back to in_progress with the same completed
            # assignment to simulate a second verification attempt hitting the
            # unique (assignment_id, repair_completed_at) constraint.
            complaint.status = Complaint.STATUS_IN_PROGRESS
            db.session.commit()

            with pytest.raises(VerificationConflictError):
                service.verify_repair(
                    complaint.id, admin.id, {"decision": ComplaintVerification.DECISION_APPROVED}
                )


class TestAdminServiceUsers:
    """Unit tests for get_all_users, get_user, and update_user."""

    def test_get_all_users_filters_by_role(self, app):
        with app.app_context():
            _mgmt_ensure_citizen("mgmt.users.citizen1@example.com")
            service = AdminService()
            result = service.get_all_users(role=Role.CITIZEN)
            assert all(item["role"] == Role.CITIZEN for item in result["items"])

    def test_get_all_users_rejects_unknown_role(self, app):
        with app.app_context():
            service = AdminService()
            with pytest.raises(ValueError, match="Unknown role"):
                service.get_all_users(role="not-a-role")

    def test_get_user_returns_details(self, app):
        with app.app_context():
            citizen = _mgmt_ensure_citizen("mgmt.users.citizen2@example.com")
            service = AdminService()
            result = service.get_user(citizen.id)
            assert result["user"]["id"] == citizen.id

    def test_get_user_rejects_missing_user(self, app):
        with app.app_context():
            service = AdminService()
            with pytest.raises(ValueError, match="not found"):
                service.get_user(999999)

    def test_update_user_edits_profile_fields(self, app):
        with app.app_context():
            citizen = _mgmt_ensure_citizen("mgmt.users.citizen3@example.com")
            admin = _mgmt_ensure_admin("mgmt.users.admin1@example.com", AdministratorProfile.SYSTEM)
            service = AdminService()
            result = service.update_user(citizen.id, admin.id, {"first_name": "Renamed"})
            assert result["user"]["first_name"] == "Renamed"

    def test_update_user_cannot_deactivate_own_account(self, app):
        with app.app_context():
            admin = _mgmt_ensure_admin("mgmt.users.admin2@example.com", AdministratorProfile.SYSTEM)
            service = AdminService()
            with pytest.raises(ValueError, match="cannot deactivate your own account"):
                service.update_user(admin.id, admin.id, {"is_active": False})

    def test_update_user_resets_password(self, app):
        with app.app_context():
            citizen = _mgmt_ensure_citizen("mgmt.users.citizen.pwreset@example.com")
            admin = _mgmt_ensure_admin("mgmt.users.admin.pwreset@example.com", AdministratorProfile.SYSTEM)
            service = AdminService()
            service.update_user(citizen.id, admin.id, {"password": "NewSecret@123"})
            refreshed = User.query.get(citizen.id)
            assert refreshed.check_password("NewSecret@123")
            assert not refreshed.check_password("Citizen@123")

    def test_update_user_updates_email(self, app):
        with app.app_context():
            citizen = _mgmt_ensure_citizen("mgmt.users.citizen.email1@example.com")
            admin = _mgmt_ensure_admin("mgmt.users.admin.email1@example.com", AdministratorProfile.SYSTEM)
            service = AdminService()
            result = service.update_user(citizen.id, admin.id, {"email": "mgmt.users.citizen.email1.new@example.com"})
            assert result["user"]["email"] == "mgmt.users.citizen.email1.new@example.com"

    def test_update_user_rejects_duplicate_email(self, app):
        with app.app_context():
            citizen_a = _mgmt_ensure_citizen("mgmt.users.citizen.dupa@example.com")
            _mgmt_ensure_citizen("mgmt.users.citizen.dupb@example.com")
            admin = _mgmt_ensure_admin("mgmt.users.admin.dup@example.com", AdministratorProfile.SYSTEM)
            service = AdminService()
            with pytest.raises(ValueError, match="already exists"):
                service.update_user(citizen_a.id, admin.id, {"email": "mgmt.users.citizen.dupb@example.com"})

    def test_update_user_municipal_admin_scoped_to_own_city_citizen(self, app):
        with app.app_context():
            city = _mgmt_ensure_city("MgmtUsersScopedCity")
            citizen = _mgmt_ensure_citizen("mgmt.users.scoped.citizen@example.com", city_id=city.id)
            muni_admin = _mgmt_ensure_admin("mgmt.users.scoped.admin@example.com", AdministratorProfile.MUNICIPAL, "MgmtUsersScopedCity")
            service = AdminService()
            result = service.update_user(citizen.id, muni_admin.id, {"first_name": "Scoped"}, acting_admin=muni_admin)
            assert result["user"]["first_name"] == "Scoped"

    def test_update_user_municipal_admin_rejects_other_city_citizen(self, app):
        with app.app_context():
            own_city = _mgmt_ensure_city("MgmtUsersOwnCity")
            other_city = _mgmt_ensure_city("MgmtUsersOtherCity")
            citizen = _mgmt_ensure_citizen("mgmt.users.othercity.citizen@example.com", city_id=other_city.id)
            muni_admin = _mgmt_ensure_admin("mgmt.users.owncity.admin@example.com", AdministratorProfile.MUNICIPAL, "MgmtUsersOwnCity")
            service = AdminService()
            with pytest.raises(ValueError, match="not found"):
                service.update_user(citizen.id, muni_admin.id, {"first_name": "Nope"}, acting_admin=muni_admin)
            assert own_city.id != other_city.id


class TestAdminServiceFieldWorkers:
    """Unit tests for get_field_workers, create_field_worker, get_field_worker,
    and update_field_worker."""

    def test_get_field_workers_scoped_to_municipal_admin_city(self, app):
        with app.app_context():
            city_a = _mgmt_ensure_city("MgmtFwCityA")
            city_b = _mgmt_ensure_city("MgmtFwCityB")
            admin = _mgmt_ensure_admin("mgmt.fw.admin1@example.com", AdministratorProfile.MUNICIPAL, "MgmtFwCityA")
            _mgmt_ensure_worker("mgmt.fw.worker1@example.com", city_a.id)
            _mgmt_ensure_worker("mgmt.fw.worker2@example.com", city_b.id)
            service = AdminService()
            result = service.get_field_workers(acting_admin=admin)
            assert all(w["city_id"] == city_a.id for w in result["field_workers"])

    def test_create_field_worker_scopes_to_admins_city(self, app):
        with app.app_context():
            _mgmt_ensure_city("MgmtFwCityC")
            admin = _mgmt_ensure_admin("mgmt.fw.admin2@example.com", AdministratorProfile.MUNICIPAL, "MgmtFwCityC")
            service = AdminService()
            result = service.create_field_worker(admin, {
                "username": "mgmt_fw_created1", "email": "mgmt.fw.created1@example.com",
                "password": "Worker@123", "first_name": "New", "last_name": "Worker",
            })
            assert result["user"]["city_id"] == admin.admin_city_id

    def test_create_field_worker_rejects_duplicate_email(self, app):
        with app.app_context():
            _mgmt_ensure_city("MgmtFwCityD")
            admin = _mgmt_ensure_admin("mgmt.fw.admin3@example.com", AdministratorProfile.MUNICIPAL, "MgmtFwCityD")
            service = AdminService()
            payload = {
                "username": "mgmt_fw_created2", "email": "mgmt.fw.created2@example.com",
                "password": "Worker@123", "first_name": "New", "last_name": "Worker",
            }
            service.create_field_worker(admin, payload)
            with pytest.raises(ValueError, match="email"):
                service.create_field_worker(admin, {**payload, "username": "mgmt_fw_created2b"})

    def test_get_field_worker_rejects_out_of_city_access(self, app):
        with app.app_context():
            _mgmt_ensure_city("MgmtFwCityE")
            city_b = _mgmt_ensure_city("MgmtFwCityF")
            admin = _mgmt_ensure_admin("mgmt.fw.admin4@example.com", AdministratorProfile.MUNICIPAL, "MgmtFwCityE")
            worker = _mgmt_ensure_worker("mgmt.fw.worker3@example.com", city_b.id)
            service = AdminService()
            with pytest.raises(ValueError, match="not found"):
                service.get_field_worker(worker.id, admin)

    def test_update_field_worker_edits_fields(self, app):
        with app.app_context():
            city = _mgmt_ensure_city("MgmtFwCityG")
            admin = _mgmt_ensure_admin("mgmt.fw.admin5@example.com", AdministratorProfile.MUNICIPAL, "MgmtFwCityG")
            worker = _mgmt_ensure_worker("mgmt.fw.worker4@example.com", city.id)
            service = AdminService()
            result = service.update_field_worker(worker.id, admin, {"is_active": False})
            assert result["user"]["is_active"] is False

    def test_update_field_worker_resets_password(self, app):
        with app.app_context():
            city = _mgmt_ensure_city("MgmtFwPwResetCity")
            admin = _mgmt_ensure_admin("mgmt.fw.pwreset.admin@example.com", AdministratorProfile.MUNICIPAL, "MgmtFwPwResetCity")
            worker = _mgmt_ensure_worker("mgmt.fw.pwreset.worker@example.com", city.id)
            service = AdminService()
            service.update_field_worker(worker.id, admin, {"password": "NewWorker@123"})
            refreshed = User.query.get(worker.id)
            assert refreshed.check_password("NewWorker@123")
            assert not refreshed.check_password("Worker@123")

    def test_update_field_worker_updates_email(self, app):
        with app.app_context():
            city = _mgmt_ensure_city("MgmtFwEmailCity")
            admin = _mgmt_ensure_admin("mgmt.fw.email.admin@example.com", AdministratorProfile.MUNICIPAL, "MgmtFwEmailCity")
            worker = _mgmt_ensure_worker("mgmt.fw.email.worker@example.com", city.id)
            service = AdminService()
            result = service.update_field_worker(worker.id, admin, {"email": "mgmt.fw.email.worker.new@example.com"})
            assert result["user"]["email"] == "mgmt.fw.email.worker.new@example.com"

    def test_update_field_worker_rejects_duplicate_email(self, app):
        with app.app_context():
            city = _mgmt_ensure_city("MgmtFwDupEmailCity")
            admin = _mgmt_ensure_admin("mgmt.fw.dupemail.admin@example.com", AdministratorProfile.MUNICIPAL, "MgmtFwDupEmailCity")
            worker_a = _mgmt_ensure_worker("mgmt.fw.dupa@example.com", city.id)
            _mgmt_ensure_worker("mgmt.fw.dupb@example.com", city.id)
            service = AdminService()
            with pytest.raises(ValueError, match="already exists"):
                service.update_field_worker(worker_a.id, admin, {"email": "mgmt.fw.dupb@example.com"})


class TestAdminServiceHierarchyAndSettings:
    """Unit tests for get_cities, get_municipal_administrators,
    get_municipal_administrator, update_municipal_administrator,
    get_system_settings, and update_system_settings."""

    def test_get_cities_returns_all_cities(self, app):
        with app.app_context():
            _mgmt_ensure_city("MgmtHierarchyCity1")
            service = AdminService()
            result = service.get_cities()
            names = {c["name"] for c in result["cities"]}
            assert "MgmtHierarchyCity1" in names

    def test_get_municipal_administrators_lists_created_admins(self, app):
        with app.app_context():
            system_admin = _mgmt_ensure_admin("mgmt.hierarchy.sysadmin1@example.com", AdministratorProfile.SYSTEM)
            service = AdminService()
            service.create_municipal_administrator(system_admin.id, {
                "username": "mgmt_hierarchy_muni1", "email": "mgmt.hierarchy.muni1@example.com",
                "password": "Municipal@123", "confirm_password": "Municipal@123",
                "first_name": "Muni", "last_name": "Admin", "pincode": "226001",
            })
            result = service.get_municipal_administrators()
            emails = {item["email"] for item in result["items"]}
            assert "mgmt.hierarchy.muni1@example.com" in emails

    def test_get_municipal_administrator_returns_details(self, app):
        with app.app_context():
            system_admin = _mgmt_ensure_admin("mgmt.hierarchy.sysadmin2@example.com", AdministratorProfile.SYSTEM)
            service = AdminService()
            created = service.create_municipal_administrator(system_admin.id, {
                "username": "mgmt_hierarchy_muni2", "email": "mgmt.hierarchy.muni2@example.com",
                "password": "Municipal@123", "confirm_password": "Municipal@123",
                "first_name": "Muni", "last_name": "Admin", "pincode": "226001",
            })
            result = service.get_municipal_administrator(created["user"]["id"])
            assert result["user"]["email"] == "mgmt.hierarchy.muni2@example.com"

    def test_update_municipal_administrator_cannot_self_deactivate(self, app):
        with app.app_context():
            system_admin = _mgmt_ensure_admin("mgmt.hierarchy.sysadmin3@example.com", AdministratorProfile.SYSTEM)
            service = AdminService()
            created = service.create_municipal_administrator(system_admin.id, {
                "username": "mgmt_hierarchy_muni3", "email": "mgmt.hierarchy.muni3@example.com",
                "password": "Municipal@123", "confirm_password": "Municipal@123",
                "first_name": "Muni", "last_name": "Admin", "pincode": "226001",
            })
            muni_id = created["user"]["id"]
            with pytest.raises(ValueError, match="cannot deactivate your own account"):
                service.update_municipal_administrator(muni_id, muni_id, {"is_active": False})

    def test_update_municipal_administrator_edits_profile(self, app):
        with app.app_context():
            system_admin = _mgmt_ensure_admin("mgmt.hierarchy.sysadmin4@example.com", AdministratorProfile.SYSTEM)
            service = AdminService()
            created = service.create_municipal_administrator(system_admin.id, {
                "username": "mgmt_hierarchy_muni4", "email": "mgmt.hierarchy.muni4@example.com",
                "password": "Municipal@123", "confirm_password": "Municipal@123",
                "first_name": "Muni", "last_name": "Admin", "pincode": "226001",
            })
            result = service.update_municipal_administrator(
                created["user"]["id"], system_admin.id, {"first_name": "Renamed"}
            )
            assert result["user"]["first_name"] == "Renamed"

    def test_update_municipal_administrator_resets_password(self, app):
        with app.app_context():
            system_admin = _mgmt_ensure_admin("mgmt.hierarchy.sysadmin.pwreset@example.com", AdministratorProfile.SYSTEM)
            service = AdminService()
            created = service.create_municipal_administrator(system_admin.id, {
                "username": "mgmt_hierarchy_muni_pwreset", "email": "mgmt.hierarchy.muni.pwreset@example.com",
                "password": "Municipal@123", "confirm_password": "Municipal@123",
                "first_name": "Muni", "last_name": "Admin", "pincode": "226001",
            })
            service.update_municipal_administrator(
                created["user"]["id"], system_admin.id, {"password": "NewMunicipal@123"}
            )
            refreshed = User.query.get(created["user"]["id"])
            assert refreshed.check_password("NewMunicipal@123")
            assert not refreshed.check_password("Municipal@123")

    def test_update_municipal_administrator_updates_email(self, app):
        with app.app_context():
            system_admin = _mgmt_ensure_admin("mgmt.hierarchy.sysadmin.email@example.com", AdministratorProfile.SYSTEM)
            service = AdminService()
            created = service.create_municipal_administrator(system_admin.id, {
                "username": "mgmt_hierarchy_muni_email", "email": "mgmt.hierarchy.muni.email@example.com",
                "password": "Municipal@123", "confirm_password": "Municipal@123",
                "first_name": "Muni", "last_name": "Admin", "pincode": "226001",
            })
            result = service.update_municipal_administrator(
                created["user"]["id"], system_admin.id, {"email": "mgmt.hierarchy.muni.email.new@example.com"}
            )
            assert result["user"]["email"] == "mgmt.hierarchy.muni.email.new@example.com"

    def test_update_municipal_administrator_rejects_duplicate_email(self, app):
        with app.app_context():
            system_admin = _mgmt_ensure_admin("mgmt.hierarchy.sysadmin.dupemail@example.com", AdministratorProfile.SYSTEM)
            service = AdminService()
            created_a = service.create_municipal_administrator(system_admin.id, {
                "username": "mgmt_hierarchy_muni_dupA", "email": "mgmt.hierarchy.muni.dupA@example.com",
                "password": "Municipal@123", "confirm_password": "Municipal@123",
                "first_name": "Muni", "last_name": "Admin", "pincode": "226001",
            })
            service.create_municipal_administrator(system_admin.id, {
                "username": "mgmt_hierarchy_muni_dupB", "email": "mgmt.hierarchy.muni.dupB@example.com",
                "password": "Municipal@123", "confirm_password": "Municipal@123",
                "first_name": "Muni", "last_name": "Admin", "pincode": "226001",
            })
            with pytest.raises(ValueError, match="already exists"):
                service.update_municipal_administrator(
                    created_a["user"]["id"], system_admin.id, {"email": "mgmt.hierarchy.muni.dupB@example.com"}
                )

    def test_get_system_settings_returns_singleton(self, app):
        with app.app_context():
            service = AdminService()
            result = service.get_system_settings()
            assert "maintenance_mode" in result["settings"]

    def test_update_system_settings_persists_changes(self, app):
        with app.app_context():
            admin = _mgmt_ensure_admin("mgmt.hierarchy.sysadmin5@example.com", AdministratorProfile.SYSTEM)
            service = AdminService()
            result = service.update_system_settings({"default_complaint_priority": "high"}, admin.id)
            assert result["settings"]["default_complaint_priority"] == "high"
            # Reset for other tests sharing the singleton settings row.
            service.update_system_settings({"default_complaint_priority": "medium"}, admin.id)
