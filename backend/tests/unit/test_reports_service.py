"""
Unit tests for ReportsService — isolated from HTTP plumbing, calling the
service layer directly against the real (in-memory) database.
"""

import pytest
from datetime import datetime, timedelta

from app.api.reports.service import ReportsService
from app.extensions import db
from app.models.city import City
from app.models.complaint import Complaint
from app.models.complaint_assignment import ComplaintAssignment
from app.models.role import Role
from app.models.user import User


def _ensure_city(name: str) -> City:
    city = City.query.filter_by(name=name).first()
    if not city:
        city = City(name=name, is_active=True)
        db.session.add(city)
        db.session.commit()
    return city


def _ensure_citizen(email: str) -> User:
    role = Role.query.filter_by(name=Role.CITIZEN).first()
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(
        username=email.split("@")[0], email=email, first_name="Test",
        last_name="Citizen", role_id=role.id, is_active=True,
    )
    user.set_password("Citizen@123")
    db.session.add(user)
    db.session.commit()
    return user


def _ensure_worker(email: str, city_id: int) -> User:
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


def _make_complaint(
    citizen_id, city_id=None, status=Complaint.STATUS_PENDING,
    category=Complaint.CATEGORY_POTHOLE, priority="medium",
    created_at=None, resolved_at=None,
) -> Complaint:
    complaint = Complaint(
        citizen_id=citizen_id, title="Test complaint",
        description="A complaint used for reports unit tests.",
        category=category, status=status, priority=priority, city_id=city_id,
    )
    if created_at:
        complaint.created_at = created_at
    db.session.add(complaint)
    db.session.commit()
    if resolved_at:
        complaint.resolved_at = resolved_at
        db.session.commit()
    return complaint


class TestReportsServiceParseDate:
    """Unit tests for ReportsService.parse_date."""

    def test_parse_date_returns_none_for_empty_value(self):
        assert ReportsService.parse_date(None) is None
        assert ReportsService.parse_date("") is None

    def test_parse_date_parses_valid_date(self):
        result = ReportsService.parse_date("2026-07-15")
        assert result == datetime(2026, 7, 15)

    def test_parse_date_end_of_day_sets_time_to_235959(self):
        result = ReportsService.parse_date("2026-07-15", end_of_day=True)
        assert result == datetime(2026, 7, 15, 23, 59, 59)

    def test_parse_date_rejects_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid date"):
            ReportsService.parse_date("15-07-2026")


class TestReportsServiceComplaintSummary:
    """Unit tests for get_complaint_summary."""

    def test_summary_counts_totals_and_breakdowns(self, app):
        with app.app_context():
            city = _ensure_city("UnitReportsCity1")
            citizen = _ensure_citizen("unit.reports.summary1@example.com")
            _make_complaint(citizen.id, city.id, status=Complaint.STATUS_PENDING, priority="urgent")
            _make_complaint(
                citizen.id, city.id, status=Complaint.STATUS_RESOLVED,
                resolved_at=datetime.utcnow(),
            )
            service = ReportsService()
            result = service.get_complaint_summary(city_id=city.id)
            assert result["total"] >= 2
            assert result["by_priority"].get("urgent", 0) >= 1
            assert result["resolved"] >= 1

    def test_summary_rejects_invalid_status_filter(self, app):
        with app.app_context():
            service = ReportsService()
            with pytest.raises(ValueError, match="Invalid status"):
                service.get_complaint_summary(status="not-a-status")

    def test_summary_zero_total_returns_zero_resolution_rate(self, app):
        with app.app_context():
            city = _ensure_city("UnitReportsEmptyCity")
            service = ReportsService()
            result = service.get_complaint_summary(city_id=city.id)
            assert result["total"] == 0
            assert result["resolution_rate"] == 0

    def test_summary_completed_uses_latest_assignment_without_double_counting(self, app):
        with app.app_context():
            city = _ensure_city("UnitReportsCompletedCity")
            citizen = _ensure_citizen("unit.reports.completed.citizen@example.com")
            worker = _ensure_worker("unit.reports.completed.worker@example.com", city.id)
            admin = _ensure_citizen("unit.reports.completed.admin@example.com")
            complaint = _make_complaint(citizen.id, city.id, status=Complaint.STATUS_IN_PROGRESS)
            db.session.add_all([
                ComplaintAssignment(
                    complaint_id=complaint.id, worker_id=worker.id,
                    assigned_by_id=admin.id, status=ComplaintAssignment.STATUS_REJECTED,
                ),
                ComplaintAssignment(
                    complaint_id=complaint.id, worker_id=worker.id,
                    assigned_by_id=admin.id, status=ComplaintAssignment.STATUS_COMPLETED,
                ),
            ])
            db.session.commit()

            result = ReportsService().get_complaint_summary(city_id=city.id)
            assert result["completed"] == 1
            assert result["closed"] == 0


class TestReportsServiceByStatusCategoryPriority:
    """Unit tests for get_complaints_by_status/category/priority."""

    def test_by_status_breakdown_percentages_sum_reasonably(self, app):
        with app.app_context():
            city = _ensure_city("UnitReportsCity2")
            citizen = _ensure_citizen("unit.reports.bystatus1@example.com")
            _make_complaint(citizen.id, city.id, status=Complaint.STATUS_PENDING)
            _make_complaint(citizen.id, city.id, status=Complaint.STATUS_ASSIGNED)
            service = ReportsService()
            result = service.get_complaints_by_status(city_id=city.id)
            statuses = {row["status"] for row in result["breakdown"]}
            assert Complaint.STATUS_PENDING in statuses
            assert Complaint.STATUS_ASSIGNED in statuses

    def test_by_category_breakdown_grouped_by_category(self, app):
        with app.app_context():
            city = _ensure_city("UnitReportsCity3")
            citizen = _ensure_citizen("unit.reports.bycategory1@example.com")
            _make_complaint(citizen.id, city.id, category=Complaint.CATEGORY_POTHOLE)
            service = ReportsService()
            result = service.get_complaints_by_category(city_id=city.id)
            categories = {row["category"] for row in result["breakdown"]}
            assert Complaint.CATEGORY_POTHOLE in categories

    def test_by_priority_breakdown_grouped_by_priority(self, app):
        with app.app_context():
            city = _ensure_city("UnitReportsCity4")
            citizen = _ensure_citizen("unit.reports.bypriority1@example.com")
            _make_complaint(citizen.id, city.id, priority="high")
            service = ReportsService()
            result = service.get_complaints_by_priority(city_id=city.id)
            priorities = {row["priority"] for row in result["breakdown"]}
            assert priorities == {"low", "medium", "high", "urgent"}
            assert next(row for row in result["breakdown"] if row["priority"] == "low")["count"] == 0

    def test_by_category_rejects_invalid_status_filter(self, app):
        with app.app_context():
            service = ReportsService()
            with pytest.raises(ValueError, match="Invalid status"):
                service.get_complaints_by_category(status="bogus")


class TestReportsServiceByLocation:
    """Unit tests for get_complaints_by_location."""

    def test_by_location_groups_by_city(self, app):
        with app.app_context():
            city = _ensure_city("UnitReportsCity5")
            citizen = _ensure_citizen("unit.reports.bylocation1@example.com")
            _make_complaint(citizen.id, city.id)
            service = ReportsService()
            result = service.get_complaints_by_location(city_id=city.id)
            names = {row["city_name"] for row in result["breakdown"]}
            assert "UnitReportsCity5" in names

    def test_by_location_flags_unassigned_complaints(self, app):
        with app.app_context():
            citizen = _ensure_citizen("unit.reports.unassigned1@example.com")
            _make_complaint(citizen.id, city_id=None)
            service = ReportsService()
            result = service.get_complaints_by_location()
            names = [row["city_name"] for row in result["breakdown"]]
            assert "Unassigned" in names


class TestReportsServiceTrends:
    """Unit tests for get_complaint_trends."""

    def test_trends_rejects_invalid_period(self, app):
        with app.app_context():
            service = ReportsService()
            with pytest.raises(ValueError, match="Invalid period"):
                service.get_complaint_trends(period="yearly")

    def test_trends_daily_returns_period_data(self, app):
        with app.app_context():
            city = _ensure_city("UnitReportsTrendsCity")
            citizen = _ensure_citizen("unit.reports.trends1@example.com")
            _make_complaint(citizen.id, city.id)
            service = ReportsService()
            result = service.get_complaint_trends(period="daily", city_id=city.id)
            assert result["period"] == "daily"
            assert isinstance(result["data"], list)

    def test_trends_with_explicit_date_range_not_clipped(self, app):
        with app.app_context():
            city = _ensure_city("UnitReportsTrendsCity2")
            citizen = _ensure_citizen("unit.reports.trends2@example.com")
            _make_complaint(citizen.id, city.id)
            service = ReportsService()
            result = service.get_complaint_trends(
                period="daily", city_id=city.id,
                date_from=datetime.utcnow() - timedelta(days=1),
                date_to=datetime.utcnow() + timedelta(days=1),
            )
            assert result["period"] == "daily"


class TestReportsServiceWorkerPerformance:
    """Unit tests for get_worker_performance."""

    def test_worker_performance_returns_stats_per_worker(self, app):
        with app.app_context():
            city = _ensure_city("UnitReportsWorkerCity")
            citizen = _ensure_citizen("unit.reports.worker.citizen1@example.com")
            worker = _ensure_worker("unit.reports.worker1@example.com", city.id)
            admin = _ensure_citizen("unit.reports.worker.admin1@example.com")
            complaint = _make_complaint(citizen.id, city.id)
            assignment = ComplaintAssignment(
                complaint_id=complaint.id, worker_id=worker.id,
                assigned_by_id=admin.id, status=ComplaintAssignment.STATUS_COMPLETED,
            )
            db.session.add(assignment)
            db.session.commit()

            service = ReportsService()
            result = service.get_worker_performance(city_id=city.id)
            worker_ids = {w["worker_id"] for w in result["workers"]}
            assert worker.id in worker_ids

    def test_worker_performance_scopes_to_city_workers_only(self, app):
        with app.app_context():
            city_a = _ensure_city("UnitReportsWorkerCityA")
            city_b = _ensure_city("UnitReportsWorkerCityB")
            worker_a = _ensure_worker("unit.reports.worker.cityA@example.com", city_a.id)
            _ensure_worker("unit.reports.worker.cityB@example.com", city_b.id)

            service = ReportsService()
            result = service.get_worker_performance(city_id=city_a.id)
            worker_ids = {w["worker_id"] for w in result["workers"]}
            assert worker_a.id in worker_ids
            assert all(
                User.query.get(w["worker_id"]).city_id == city_a.id
                for w in result["workers"]
            )


class TestReportsServiceExportDataset:
    """Unit tests for build_export_dataset and export_csv."""

    def test_build_export_dataset_assembles_all_sections(self, app):
        with app.app_context():
            city = _ensure_city("UnitReportsExportCity")
            citizen = _ensure_citizen("unit.reports.export1@example.com")
            _make_complaint(citizen.id, city.id)
            service = ReportsService()
            dataset = service.build_export_dataset(city_id=city.id)
            for key in ("summary", "by_status", "by_category", "by_priority", "by_location", "workers"):
                assert key in dataset

    def test_export_csv_produces_valid_csv_text(self, app):
        with app.app_context():
            city = _ensure_city("UnitReportsExportCity2")
            citizen = _ensure_citizen("unit.reports.export2@example.com")
            _make_complaint(citizen.id, city.id)
            service = ReportsService()
            dataset = service.build_export_dataset(city_id=city.id)
            csv_text = service.export_csv(dataset)
            assert "Civic Services Platform" in csv_text
            assert "Summary" in csv_text
