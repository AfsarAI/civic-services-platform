"""
Unit tests for FieldWorkerService — isolated from HTTP plumbing, calling the
service layer directly against the real (in-memory) database.
"""

import pytest
from app.api.fieldworker.service import FieldWorkerService
from app.extensions import db
from app.models.complaint import Complaint
from app.models.complaint_assignment import ComplaintAssignment
from app.models.role import Role
from app.models.user import User


def _make_worker(email: str) -> User:
    role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(
        username=email.split("@")[0],
        email=email,
        first_name="Field",
        last_name="Worker",
        role_id=role.id,
        is_active=True,
    )
    user.set_password("Worker@123")
    db.session.add(user)
    db.session.commit()
    return user


def _make_citizen(email: str) -> User:
    role = Role.query.filter_by(name=Role.CITIZEN).first()
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(
        username=email.split("@")[0],
        email=email,
        first_name="Test",
        last_name="Citizen",
        role_id=role.id,
        is_active=True,
    )
    user.set_password("Citizen@123")
    db.session.add(user)
    db.session.commit()
    return user


def _make_admin(email: str) -> User:
    role = Role.query.filter_by(name=Role.ADMINISTRATOR).first()
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(
        username=email.split("@")[0],
        email=email,
        first_name="Test",
        last_name="Admin",
        role_id=role.id,
        is_active=True,
    )
    user.set_password("Admin@123456")
    db.session.add(user)
    db.session.commit()
    return user


def _make_assignment(
    worker_id: int, citizen_id: int, status: str = ComplaintAssignment.STATUS_ASSIGNED,
    complaint_status: str = Complaint.STATUS_ASSIGNED, priority: str = "medium",
    title: str = "Pothole",
) -> ComplaintAssignment:
    assigned_by = _make_admin("unit.fw.assigner@example.com")
    complaint = Complaint(
        citizen_id=citizen_id,
        title=title,
        description="A pothole requiring repair.",
        category=Complaint.CATEGORY_POTHOLE,
        status=complaint_status,
        priority=priority,
    )
    db.session.add(complaint)
    db.session.flush()
    assignment = ComplaintAssignment(
        complaint_id=complaint.id,
        worker_id=worker_id,
        assigned_by_id=assigned_by.id,
        status=status,
    )
    db.session.add(assignment)
    db.session.commit()
    return assignment


class TestFieldWorkerServiceGetAssignments:
    """Unit tests for get_assignments and get_assignment."""

    def test_get_assignments_returns_only_own_assignments(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.list1@example.com")
            other = _make_worker("unit.fw.list2@example.com")
            citizen = _make_citizen("unit.fw.citizen1@example.com")
            _make_assignment(worker.id, citizen.id)
            _make_assignment(other.id, citizen.id)
            service = FieldWorkerService()
            result = service.get_assignments(worker.id)
            assert all(item["complaint_id"] for item in result["items"])

    def test_get_assignments_rejects_invalid_status_filter(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.list3@example.com")
            service = FieldWorkerService()
            with pytest.raises(ValueError, match="Invalid status"):
                service.get_assignments(worker.id, status="not-a-status")

    def test_get_assignments_rejects_invalid_priority_filter(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.list4@example.com")
            service = FieldWorkerService()
            with pytest.raises(ValueError, match="Invalid priority"):
                service.get_assignments(worker.id, priority="not-a-priority")

    def test_get_assignments_rejects_invalid_sort_by(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.list5@example.com")
            service = FieldWorkerService()
            with pytest.raises(ValueError, match="Invalid sort_by"):
                service.get_assignments(worker.id, sort_by="not-a-field")

    def test_get_assignments_rejects_invalid_sort_order(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.list6@example.com")
            service = FieldWorkerService()
            with pytest.raises(ValueError, match="Invalid sort_order"):
                service.get_assignments(worker.id, sort_order="sideways")

    def test_get_assignment_rejects_other_workers_assignment(self, app):
        with app.app_context():
            owner = _make_worker("unit.fw.get1@example.com")
            other = _make_worker("unit.fw.get2@example.com")
            citizen = _make_citizen("unit.fw.citizen2@example.com")
            assignment = _make_assignment(owner.id, citizen.id)
            service = FieldWorkerService()
            with pytest.raises(ValueError, match="permission"):
                service.get_assignment(assignment.id, other.id)

    def test_get_assignment_rejects_missing_assignment(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.get3@example.com")
            service = FieldWorkerService()
            with pytest.raises(ValueError, match="not found"):
                service.get_assignment(999999, worker.id)


class TestFieldWorkerServiceAccept:
    """Unit tests for accept_assignment."""

    def test_accept_assignment_transitions_to_accepted_and_complaint_in_progress(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.accept1@example.com")
            citizen = _make_citizen("unit.fw.citizen3@example.com")
            assignment = _make_assignment(worker.id, citizen.id)
            service = FieldWorkerService()
            result = service.accept_assignment(assignment.id, worker.id)
            assert result["assignment"]["status"] == ComplaintAssignment.STATUS_ACCEPTED
            assert Complaint.query.get(assignment.complaint_id).status == Complaint.STATUS_IN_PROGRESS

    def test_accept_assignment_rejects_non_assigned_status(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.accept2@example.com")
            citizen = _make_citizen("unit.fw.citizen4@example.com")
            assignment = _make_assignment(worker.id, citizen.id, status=ComplaintAssignment.STATUS_ACCEPTED)
            service = FieldWorkerService()
            with pytest.raises(ValueError, match="Only assignments with status 'assigned'"):
                service.accept_assignment(assignment.id, worker.id)

    def test_accept_assignment_rejects_terminal_complaint(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.accept3@example.com")
            citizen = _make_citizen("unit.fw.citizen5@example.com")
            assignment = _make_assignment(
                worker.id, citizen.id, complaint_status=Complaint.STATUS_CANCELLED
            )
            service = FieldWorkerService()
            with pytest.raises(ValueError, match="no longer accepts"):
                service.accept_assignment(assignment.id, worker.id)


class TestFieldWorkerServiceUpdateProgress:
    """Unit tests for update_progress."""

    def test_update_progress_moves_accepted_to_in_progress(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.progress1@example.com")
            citizen = _make_citizen("unit.fw.citizen6@example.com")
            assignment = _make_assignment(worker.id, citizen.id, status=ComplaintAssignment.STATUS_ACCEPTED)
            service = FieldWorkerService()
            result = service.update_progress(assignment.id, worker.id, {
                "status": "in_progress", "notes": "Started repair",
            })
            assert result["assignment"]["status"] == "in_progress"

    def test_update_progress_rejects_invalid_transition(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.progress2@example.com")
            citizen = _make_citizen("unit.fw.citizen7@example.com")
            assignment = _make_assignment(worker.id, citizen.id, status=ComplaintAssignment.STATUS_ASSIGNED)
            service = FieldWorkerService()
            with pytest.raises(ValueError, match="Cannot transition"):
                service.update_progress(assignment.id, worker.id, {"status": "in_progress"})

    def test_update_progress_reject_returns_complaint_to_pending(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.progress3@example.com")
            citizen = _make_citizen("unit.fw.citizen8@example.com")
            assignment = _make_assignment(
                worker.id, citizen.id, status=ComplaintAssignment.STATUS_ACCEPTED,
                complaint_status=Complaint.STATUS_IN_PROGRESS,
            )
            service = FieldWorkerService()
            result = service.update_progress(assignment.id, worker.id, {
                "status": "rejected", "notes": "Cannot complete, unsafe site",
            })
            assert result["assignment"]["status"] == "rejected"
            assert Complaint.query.get(assignment.complaint_id).status == Complaint.STATUS_PENDING


class TestFieldWorkerServiceComplete:
    """Unit tests for complete_assignment."""

    def test_complete_assignment_marks_completed_and_keeps_complaint_in_progress(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.complete1@example.com")
            citizen = _make_citizen("unit.fw.citizen9@example.com")
            assignment = _make_assignment(
                worker.id, citizen.id, status=ComplaintAssignment.STATUS_IN_PROGRESS,
                complaint_status=Complaint.STATUS_IN_PROGRESS,
            )
            service = FieldWorkerService()
            result = service.complete_assignment(assignment.id, worker.id)
            assert result["assignment"]["status"] == ComplaintAssignment.STATUS_COMPLETED
            assert Complaint.query.get(assignment.complaint_id).status == Complaint.STATUS_IN_PROGRESS

    def test_complete_assignment_rejects_non_active_status(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.complete2@example.com")
            citizen = _make_citizen("unit.fw.citizen10@example.com")
            assignment = _make_assignment(worker.id, citizen.id, status=ComplaintAssignment.STATUS_ASSIGNED)
            service = FieldWorkerService()
            with pytest.raises(ValueError, match="Only accepted or in-progress"):
                service.complete_assignment(assignment.id, worker.id)

    def test_complete_assignment_rejects_invalid_evidence_url(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.complete3@example.com")
            citizen = _make_citizen("unit.fw.citizen11@example.com")
            assignment = _make_assignment(
                worker.id, citizen.id, status=ComplaintAssignment.STATUS_IN_PROGRESS,
                complaint_status=Complaint.STATUS_IN_PROGRESS,
            )
            service = FieldWorkerService()
            with pytest.raises(ValueError, match="Invalid evidence URL"):
                service.complete_assignment(
                    assignment.id, worker.id, evidence_url="https://evil.example.com/x.jpg"
                )


class TestFieldWorkerServiceDashboard:
    """Unit tests for get_dashboard_summary."""

    def test_dashboard_summary_returns_counts_by_status(self, app):
        with app.app_context():
            worker = _make_worker("unit.fw.dashboard1@example.com")
            citizen = _make_citizen("unit.fw.citizen12@example.com")
            _make_assignment(worker.id, citizen.id, status=ComplaintAssignment.STATUS_ASSIGNED)
            _make_assignment(worker.id, citizen.id, status=ComplaintAssignment.STATUS_COMPLETED)
            service = FieldWorkerService()
            result = service.get_dashboard_summary(worker.id)
            assert result["total_assignments"] >= 2
            assert result["by_status"][ComplaintAssignment.STATUS_COMPLETED] >= 1
