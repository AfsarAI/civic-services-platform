"""
Unit tests for the KPI calculation helpers used by the admin dashboard
(TPS-97 Performance Metrics Dashboard): average resolution/assignment time,
closure rate, citizen satisfaction rating.
"""

from datetime import datetime, timedelta, timezone

from app.api.administrator.service import AdminService
from app.extensions import db
from app.models.city import City
from app.models.complaint import Complaint
from app.models.complaint_assignment import ComplaintAssignment
from app.models.feedback import Feedback
from app.models.role import Role
from app.models.user import User


class TestAdminDashboardKpiHelpers:
    """Unit tests for AdminService._calculate_* KPI helper methods."""

    @staticmethod
    def _ensure_city(name: str) -> City:
        city = City.query.filter_by(name=name).first()
        if not city:
            city = City(name=name, is_active=True)
            db.session.add(city)
            db.session.commit()
        return city

    @classmethod
    def _ensure_citizen(cls, email: str) -> User:
        role = Role.query.filter_by(name=Role.CITIZEN).first()
        user = User.query.filter_by(email=email).first()
        if user:
            return user
        user = User(
            username=email.split("@")[0],
            email=email,
            first_name="Citizen",
            last_name="Tester",
            role_id=role.id,
            is_active=True,
        )
        user.set_password("Citizen@123")
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def _ensure_worker(cls, email: str, city_id: int) -> User:
        role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
        user = User.query.filter_by(email=email).first()
        if user:
            return user
        user = User(
            username=email.split("@")[0],
            email=email,
            first_name="Worker",
            last_name="Tester",
            role_id=role.id,
            city_id=city_id,
            is_active=True,
        )
        user.set_password("Worker@123")
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def _make_complaint(
        cls, citizen_id, city_id, status=Complaint.STATUS_PENDING,
        priority="medium", created_hours_ago=0, resolved_hours_after=None,
    ):
        created_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=created_hours_ago)
        complaint = Complaint(
            title="Test pothole",
            description="Deep pothole requiring repair.",
            category=Complaint.CATEGORY_POTHOLE,
            status=status,
            priority=priority,
            city_id=city_id,
            citizen_id=citizen_id,
            created_at=created_at,
        )
        if resolved_hours_after is not None:
            complaint.resolved_at = created_at + timedelta(hours=resolved_hours_after)
        db.session.add(complaint)
        db.session.commit()
        return complaint

    def test_avg_resolution_time_averages_only_resolved_complaints(self, app):
        with app.app_context():
            city = self._ensure_city("KpiCityA")
            citizen = self._ensure_citizen("kpi-citizen-a@example.com")

            self._make_complaint(citizen.id, city.id, status=Complaint.STATUS_RESOLVED, resolved_hours_after=10)
            self._make_complaint(citizen.id, city.id, status=Complaint.STATUS_RESOLVED, resolved_hours_after=20)
            self._make_complaint(citizen.id, city.id, status=Complaint.STATUS_PENDING)

            service = AdminService()
            query = Complaint.query.filter_by(city_id=city.id)
            avg_hours = service._calculate_avg_resolution_time(query)

            assert avg_hours == 15.0

    def test_avg_resolution_time_also_includes_closed_complaints(self, app):
        """A complaint that moved on to 'closed' still had a resolution time."""
        with app.app_context():
            city = self._ensure_city("KpiCityH")
            citizen = self._ensure_citizen("kpi-citizen-h@example.com")

            self._make_complaint(citizen.id, city.id, status=Complaint.STATUS_RESOLVED, resolved_hours_after=10)
            self._make_complaint(citizen.id, city.id, status=Complaint.STATUS_CLOSED, resolved_hours_after=30)

            service = AdminService()
            query = Complaint.query.filter_by(city_id=city.id)
            avg_hours = service._calculate_avg_resolution_time(query)

            assert avg_hours == 20.0

    def test_avg_resolution_time_zero_when_no_resolved_complaints(self, app):
        with app.app_context():
            city = self._ensure_city("KpiCityB")
            citizen = self._ensure_citizen("kpi-citizen-b@example.com")
            self._make_complaint(citizen.id, city.id, status=Complaint.STATUS_PENDING)

            service = AdminService()
            query = Complaint.query.filter_by(city_id=city.id)
            assert service._calculate_avg_resolution_time(query) == 0.0

    def test_avg_assignment_time_averages_accepted_assignments(self, app):
        with app.app_context():
            city = self._ensure_city("KpiCityC")
            citizen = self._ensure_citizen("kpi-citizen-c@example.com")
            worker = self._ensure_worker("kpi-worker-c@example.com", city.id)
            admin_ref = worker  # any user id works as assigned_by for this unit test

            complaint = self._make_complaint(citizen.id, city.id, status=Complaint.STATUS_ASSIGNED)
            assigned_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=5)
            assignment = ComplaintAssignment(
                complaint_id=complaint.id,
                worker_id=worker.id,
                assigned_by_id=admin_ref.id,
                status=ComplaintAssignment.STATUS_ACCEPTED,
                assigned_at=assigned_at,
                accepted_at=assigned_at + timedelta(hours=3),
            )
            db.session.add(assignment)
            db.session.commit()

            service = AdminService()
            query = Complaint.query.filter_by(city_id=city.id)
            avg_hours = service._calculate_avg_assignment_time(query)

            assert avg_hours == 3.0

    def test_avg_assignment_time_zero_when_no_accepted_assignments(self, app):
        with app.app_context():
            city = self._ensure_city("KpiCityD")
            citizen = self._ensure_citizen("kpi-citizen-d@example.com")
            self._make_complaint(citizen.id, city.id, status=Complaint.STATUS_PENDING)

            service = AdminService()
            query = Complaint.query.filter_by(city_id=city.id)
            assert service._calculate_avg_assignment_time(query) == 0.0

    def test_closure_rate_percentage_calculation(self):
        service = AdminService()
        counts = {
            Complaint.STATUS_PENDING: 2,
            Complaint.STATUS_ASSIGNED: 1,
            Complaint.STATUS_IN_PROGRESS: 1,
            Complaint.STATUS_RESOLVED: 3,
            Complaint.STATUS_CLOSED: 3,
            Complaint.STATUS_REJECTED: 0,
            Complaint.STATUS_CANCELLED: 0,
        }
        total = sum(counts.values())
        rate = service._calculate_closure_rate(counts, total)
        assert rate == 60.0

    def test_closure_rate_zero_when_total_zero(self):
        service = AdminService()
        assert service._calculate_closure_rate({}, 0) == 0.0

    def test_avg_satisfaction_rating_averages_feedback_for_city(self, app):
        with app.app_context():
            city = self._ensure_city("KpiCityE")
            other_city = self._ensure_city("KpiCityF")
            citizen = self._ensure_citizen("kpi-citizen-e@example.com")

            complaint_in_city = self._make_complaint(
                citizen.id, city.id, status=Complaint.STATUS_RESOLVED, resolved_hours_after=5
            )
            complaint_other_city = self._make_complaint(
                citizen.id, other_city.id, status=Complaint.STATUS_RESOLVED, resolved_hours_after=5
            )

            db.session.add(Feedback(complaint_id=complaint_in_city.id, citizen_id=citizen.id, rating=4))
            db.session.add(Feedback(complaint_id=complaint_other_city.id, citizen_id=citizen.id, rating=2))
            db.session.commit()

            service = AdminService()
            city_scoped_rating = service._calculate_avg_satisfaction_rating(city_id=city.id)
            other_city_scoped_rating = service._calculate_avg_satisfaction_rating(city_id=other_city.id)

            # City scoping must isolate ratings per city; the unscoped total
            # (used by system admins) is not asserted here because the shared
            # test database accumulates feedback from other test modules.
            assert city_scoped_rating == 4.0
            assert other_city_scoped_rating == 2.0

    def test_avg_satisfaction_rating_zero_when_no_feedback(self, app):
        with app.app_context():
            city = self._ensure_city("KpiCityG")
            service = AdminService()
            assert service._calculate_avg_satisfaction_rating(city_id=city.id) == 0.0
