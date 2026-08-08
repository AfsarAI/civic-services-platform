"""
Unit tests for SQLAlchemy models.
"""

from datetime import datetime, timezone

from app.models.administrator_profile import AdministratorProfile
from app.models.city import City
from app.models.city_pincode import CityPincode
from app.models.complaint import Complaint
from app.models.complaint_assignment import ComplaintAssignment
from app.models.complaint_verification import ComplaintVerification
from app.models.feedback import Feedback
from app.models.notification import Notification
from app.models.role import Role
from app.models.system_setting import SystemSetting
from app.models.user import User
from app.extensions import db


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

    def test_non_administrator_has_no_admin_level_or_city(self, app):
        with app.app_context():
            user = User(first_name="Regular", last_name="Citizen", role_id=1)
            user.role = Role(name=Role.CITIZEN)
            assert user.is_administrator is False
            assert user.admin_level is None
            assert user.is_system_admin is False

    def test_system_admin_has_no_city(self, app):
        with app.app_context():
            profile = AdministratorProfile(admin_level=AdministratorProfile.SYSTEM, city=None)
            user = User(first_name="System", last_name="Admin", role_id=1)
            user.role = Role(name=Role.ADMINISTRATOR)
            user.admin_profile = profile
            assert user.is_system_admin is True
            assert user.admin_city_name is None


class TestComplaintModel:
    """Unit tests for the Complaint model."""

    def test_status_constants_defined(self):
        assert Complaint.STATUS_PENDING == "pending"
        assert Complaint.STATUS_RESOLVED == "resolved"

    def test_valid_statuses_list(self):
        assert "pending" in Complaint.VALID_STATUSES
        assert "resolved" in Complaint.VALID_STATUSES
        assert "cancelled" in Complaint.VALID_STATUSES
        assert len(Complaint.VALID_STATUSES) == 7

    def test_complaint_repr(self, app):
        with app.app_context():
            complaint = Complaint(
                title="Pothole", description="A pothole.", category=Complaint.CATEGORY_POTHOLE,
                status=Complaint.STATUS_PENDING, priority="medium",
            )
            assert "Complaint" in repr(complaint)


class TestComplaintVerificationModel:
    def test_decision_constants_defined(self):
        assert ComplaintVerification.DECISION_APPROVED == "approved"
        assert (
            ComplaintVerification.DECISION_REWORK_REQUESTED
            == "rework_requested"
        )


class TestCityModel:
    """Unit tests for the City model."""

    def test_city_repr(self, app):
        with app.app_context():
            city = City(name="Kanpur", is_active=True)
            assert "Kanpur" in repr(city)


class TestCityPincodeModel:
    """Unit tests for the CityPincode model."""

    def test_city_pincode_repr(self, app):
        with app.app_context():
            city = City(name="Varanasi", is_active=True)
            db.session.add(city)
            db.session.flush()
            mapping = CityPincode(pincode="221001", city_id=city.id, is_active=True)
            assert "221001" in repr(mapping)
            assert str(city.id) in repr(mapping)


class TestComplaintAssignmentModel:
    """Unit tests for the ComplaintAssignment model."""

    def test_status_constants_defined(self):
        assert ComplaintAssignment.STATUS_ASSIGNED == "assigned"
        assert ComplaintAssignment.STATUS_ACCEPTED == "accepted"
        assert ComplaintAssignment.STATUS_IN_PROGRESS == "in_progress"
        assert ComplaintAssignment.STATUS_COMPLETED == "completed"
        assert ComplaintAssignment.STATUS_REJECTED == "rejected"

    def test_assignment_repr(self, app):
        with app.app_context():
            assignment = ComplaintAssignment(complaint_id=1, worker_id=2, assigned_by_id=3)
            assert "complaint=1" in repr(assignment)
            assert "worker=2" in repr(assignment)


class TestFeedbackModel:
    """Unit tests for the Feedback model."""

    def test_feedback_repr(self, app):
        with app.app_context():
            feedback = Feedback(complaint_id=1, citizen_id=2, rating=5)
            assert "rating=5" in repr(feedback)


class TestNotificationModel:
    """Unit tests for the Notification model."""

    def test_notification_type_constants_defined(self):
        assert Notification.TYPE_COMPLAINT_SUBMITTED == "complaint_submitted"
        assert Notification.TYPE_COMPLAINT_ASSIGNED == "complaint_assigned"
        assert Notification.TYPE_STATUS_UPDATE == "status_update"
        assert Notification.TYPE_COMPLAINT_RESOLVED == "complaint_resolved"
        assert Notification.TYPE_GENERAL == "general"

    def test_notification_repr(self, app):
        with app.app_context():
            notification = Notification(id=7, user_id=3, title="T", message="M")
            assert "7" in repr(notification)
            assert "user=3" in repr(notification)


class TestSystemSettingModel:
    """Unit tests for the SystemSetting model."""

    def test_system_setting_repr(self, app):
        with app.app_context():
            setting = SystemSetting(site_name="My Platform")
            assert "My Platform" in repr(setting)


class TestAdministratorProfileModel:
    """Unit tests for the AdministratorProfile model."""

    def test_valid_levels_defined(self):
        assert AdministratorProfile.SYSTEM == "system"
        assert AdministratorProfile.MUNICIPAL == "municipal"
        assert AdministratorProfile.VALID_LEVELS == ("system", "municipal")

    def test_is_system_admin_and_is_municipal_admin_properties(self, app):
        with app.app_context():
            system_profile = AdministratorProfile(admin_level=AdministratorProfile.SYSTEM)
            municipal_profile = AdministratorProfile(admin_level=AdministratorProfile.MUNICIPAL)
            assert system_profile.is_system_admin is True
            assert system_profile.is_municipal_admin is False
            assert municipal_profile.is_system_admin is False
            assert municipal_profile.is_municipal_admin is True

    def test_administrator_profile_repr(self, app):
        with app.app_context():
            profile = AdministratorProfile(user_id=5, admin_level=AdministratorProfile.SYSTEM)
            assert "user_id=5" in repr(profile)
            assert "system" in repr(profile)


class TestUTCDateTime:
    """Regression tests for the UTCDateTime column type (Milestone 4 timezone fix).

    Before this fix, datetimes stored via plain ``db.DateTime`` came back from
    SQLite as naive (no tzinfo), so ``.isoformat()`` omitted the UTC offset and
    the frontend's ``new Date(...)`` misparsed it as local time (a 5:30h drift
    for IST). ``UTCDateTime`` guarantees every loaded value is tz-aware UTC.
    """

    def _make_role(self):
        role = Role.query.filter_by(name=Role.CITIZEN).first()
        if not role:
            role = Role(name=Role.CITIZEN)
            db.session.add(role)
            db.session.commit()
        return role

    def test_user_created_at_round_trips_as_timezone_aware(self, app):
        with app.app_context():
            role = self._make_role()
            user = User(
                username="utcuser", email="utc.user@example.com",
                first_name="UTC", last_name="User", role_id=role.id,
            )
            user.set_password("Secret@123")
            db.session.add(user)
            db.session.commit()

            db.session.expire_all()
            reloaded = User.query.filter_by(email="utc.user@example.com").first()
            assert reloaded.created_at.tzinfo is not None
            assert reloaded.created_at.isoformat().endswith("+00:00")

    def test_complaint_assignment_expected_completion_round_trips_as_timezone_aware(self, app):
        with app.app_context():
            role = self._make_role()
            worker_role = Role.query.filter_by(name=Role.FIELD_WORKER).first() or Role(name=Role.FIELD_WORKER)
            if not worker_role.id:
                db.session.add(worker_role)
                db.session.commit()
            citizen = User(
                username="utccitizen", email="utc.citizen@example.com",
                first_name="UTC", last_name="Citizen", role_id=role.id,
            )
            citizen.set_password("Secret@123")
            worker = User(
                username="utcworker", email="utc.worker@example.com",
                first_name="UTC", last_name="Worker", role_id=worker_role.id,
            )
            worker.set_password("Secret@123")
            db.session.add_all([citizen, worker])
            db.session.flush()

            complaint = Complaint(
                citizen_id=citizen.id, title="UTC test pothole",
                description="A complaint used to verify timezone-aware datetimes.",
                category=Complaint.CATEGORY_POTHOLE, status=Complaint.STATUS_ASSIGNED,
            )
            db.session.add(complaint)
            db.session.flush()

            expected_completion = datetime(2026, 8, 1, 11, 30, 0, tzinfo=timezone.utc)
            assignment = ComplaintAssignment(
                complaint_id=complaint.id, worker_id=worker.id, assigned_by_id=worker.id,
                expected_completion_at=expected_completion,
            )
            db.session.add(assignment)
            db.session.commit()

            db.session.expire_all()
            reloaded = ComplaintAssignment.query.get(assignment.id)
            assert reloaded.expected_completion_at.tzinfo is not None
            assert reloaded.expected_completion_at.isoformat() == "2026-08-01T11:30:00+00:00"
