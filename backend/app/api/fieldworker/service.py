"""
Field Worker service — business logic for field-worker-facing operations.
"""

from datetime import datetime, timezone

from app.api.notifications.service import NotificationService
from app.extensions import db
from app.models.complaint import Complaint
from app.models.complaint_assignment import ComplaintAssignment
from app.models.notification import Notification
from app.services.system_settings_service import SystemSettingsService


class FieldWorkerService:
    """Handles assignment tracking and progress updates for field workers."""

    def __init__(self):
        self.notifications = NotificationService()

    # ── List assignments ──────────────────────────────────────────────────

    def get_assignments(
        self,
        worker_id: int,
        page: int = 1,
        per_page: int = 20,
        status: str = None,
    ) -> dict:
        """Return paginated assignments for this field worker.

        Args:
            worker_id: ID of the authenticated field worker.
            page: 1-based page number.
            per_page: Page size (capped at 100).
            status: Optional status filter.
        """
        per_page = min(per_page, 100)
        valid_statuses = [
            ComplaintAssignment.STATUS_ASSIGNED,
            ComplaintAssignment.STATUS_ACCEPTED,
            ComplaintAssignment.STATUS_IN_PROGRESS,
            ComplaintAssignment.STATUS_COMPLETED,
            ComplaintAssignment.STATUS_REJECTED,
        ]
        query = ComplaintAssignment.query.filter_by(worker_id=worker_id)

        if status:
            if status not in valid_statuses:
                raise ValueError(f"Invalid status '{status}'.")
            query = query.filter_by(status=status)

        query = query.order_by(ComplaintAssignment.assigned_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": [self._serialize(a, full=True) for a in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
        }

    # ── Get single assignment ─────────────────────────────────────────────

    def get_assignment(self, assignment_id: int, worker_id: int) -> dict:
        """Return a single assignment owned by this field worker.

        Raises:
            ValueError: If not found or not owned by this worker.
        """
        assignment = self._get_owned(assignment_id, worker_id)
        return {"assignment": self._serialize(assignment, full=True)}

    # ── Accept assignment ─────────────────────────────────────────────────

    def accept_assignment(self, assignment_id: int, worker_id: int) -> dict:
        """Accept an assigned task.

        Transitions: assignment ``assigned`` → ``accepted``.
        Also moves the complaint to ``in_progress``.

        Raises:
            ValueError: Business rule violations.
        """
        # Process field worker acceptance of assigned complaint task.
        assignment = self._get_owned(assignment_id, worker_id)
        self._ensure_complaint_actionable(assignment.complaint)

        if assignment.status != ComplaintAssignment.STATUS_ASSIGNED:
            raise ValueError(
                "Only assignments with status 'assigned' can be accepted. "
                f"Current status: '{assignment.status}'."
            )

        assignment.status = ComplaintAssignment.STATUS_ACCEPTED
        assignment.accepted_at = datetime.now(timezone.utc)

        # Reflect on the complaint
        complaint = assignment.complaint
        if complaint and complaint.status == Complaint.STATUS_ASSIGNED:
            complaint.status = Complaint.STATUS_IN_PROGRESS

        db.session.commit()

        if complaint and SystemSettingsService.notifications_enabled():
            self.notifications.send_notification(
                user_id=complaint.citizen_id,
                title="Repair work started",
                message=f"Work has started on your complaint #{complaint.id} '{complaint.title}'.",
                notification_type=Notification.TYPE_STATUS_UPDATE,
                related_complaint_id=complaint.id,
            )

        return {"assignment": self._serialize(assignment, full=True)}

    # ── Update progress ───────────────────────────────────────────────────

    def update_progress(
        self, assignment_id: int, worker_id: int, data: dict
    ) -> dict:
        """Update assignment status and/or notes.

        Allowed status transitions via this endpoint:
        - ``accepted`` → ``in_progress``
        - ``accepted`` or ``in_progress`` → ``rejected``

        When rejecting, the complaint is returned to ``pending`` for
        re-assignment by an administrator.

        Raises:
            ValueError: Business rule violations.
        """
        assignment = self._get_owned(assignment_id, worker_id)
        # Process progress status updates and field notes for assigned repair tasks.
        self._ensure_complaint_actionable(assignment.complaint)
        new_status = data["status"]

        valid_from = {
            "in_progress": [ComplaintAssignment.STATUS_ACCEPTED],
            "rejected": [
                ComplaintAssignment.STATUS_ASSIGNED,
                ComplaintAssignment.STATUS_ACCEPTED,
                ComplaintAssignment.STATUS_IN_PROGRESS,
            ],
        }

        if assignment.status not in valid_from[new_status]:
            raise ValueError(
                f"Cannot transition from '{assignment.status}' to '{new_status}'."
            )

        assignment.status = new_status
        if "notes" in data and data["notes"] is not None:
            assignment.notes = data["notes"]

        complaint = assignment.complaint
        if new_status == "rejected" and complaint:
            complaint.status = Complaint.STATUS_PENDING

        db.session.commit()

        if new_status == "rejected" and complaint and SystemSettingsService.notifications_enabled():
            self.notifications.send_notification(
                user_id=complaint.citizen_id,
                title="Complaint reassignment pending",
                message=(
                    f"Your complaint #{complaint.id} '{complaint.title}' was returned for reassignment "
                    "to another field worker."
                ),
                notification_type=Notification.TYPE_STATUS_UPDATE,
                related_complaint_id=complaint.id,
            )
            if assignment.assigned_by_id:
                self.notifications.send_notification(
                    user_id=assignment.assigned_by_id,
                    title="Assignment rejected — reassignment needed",
                    message=(
                        f"The field worker rejected the task for complaint #{complaint.id} "
                        f"'{complaint.title}'. Please assign it to another field worker."
                    ),
                    notification_type=Notification.TYPE_STATUS_UPDATE,
                    related_complaint_id=complaint.id,
                )

        return {"assignment": self._serialize(assignment, full=True)}

    # ── Complete assignment ───────────────────────────────────────────────

    def complete_assignment(
        self, assignment_id: int, worker_id: int, evidence_url: str = None
    ) -> dict:
        """Mark an assignment as completed.

        Transitions: ``accepted`` or ``in_progress`` → ``completed``.
        Sets ``completed_at`` and, if provided, ``evidence_url`` (photo proof
        of the repair work, uploaded via ``POST /fieldworker/assignments/media``).
        The complaint status remains ``in_progress`` until an administrator
        marks it as resolved. The administrator who made the assignment is
        notified so they know verification is needed.

        Raises:
            ValueError: Business rule violations.
        """
        assignment = self._get_owned(assignment_id, worker_id)
        # Record completion of repair work assignment and attach optional evidence.
        self._ensure_complaint_actionable(assignment.complaint)

        if assignment.status not in (
            ComplaintAssignment.STATUS_ACCEPTED,
            ComplaintAssignment.STATUS_IN_PROGRESS,
        ):
            raise ValueError(
                "Only accepted or in-progress assignments can be completed. "
                f"Current status: '{assignment.status}'."
            )

        assignment.status = ComplaintAssignment.STATUS_COMPLETED
        assignment.completed_at = datetime.now(timezone.utc)
        if evidence_url:
            if not evidence_url.startswith("/api/v1/fieldworker/assignments/media/"):
                raise ValueError("Invalid evidence URL.")
            assignment.evidence_url = evidence_url

        db.session.commit()

        complaint = assignment.complaint
        if (
            complaint
            and assignment.assigned_by_id
            and SystemSettingsService.notifications_enabled()
        ):
            self.notifications.send_notification(
                user_id=assignment.assigned_by_id,
                title="Repair marked complete — verification needed",
                message=(
                    f"The field worker has marked complaint #{complaint.id} '{complaint.title}' as "
                    "complete. Please review and verify before resolving the complaint."
                ),
                notification_type=Notification.TYPE_STATUS_UPDATE,
                related_complaint_id=complaint.id,
            )
            self.notifications.send_notification(
                user_id=complaint.citizen_id,
                title="Repair work completed",
                message=(
                    f"Repair work for your complaint #{complaint.id} '{complaint.title}' has been "
                    "completed by the field worker and is awaiting administrator verification."
                ),
                notification_type=Notification.TYPE_STATUS_UPDATE,
                related_complaint_id=complaint.id,
            )

        return {"assignment": self._serialize(assignment, full=True)}

    # ── Dashboard ─────────────────────────────────────────────────────────

    def get_dashboard_summary(self, worker_id: int) -> dict:
        """Return assignment counts by status for this field worker."""
        base = ComplaintAssignment.query.filter_by(worker_id=worker_id)

        statuses = [
            ComplaintAssignment.STATUS_ASSIGNED,
            ComplaintAssignment.STATUS_ACCEPTED,
            ComplaintAssignment.STATUS_IN_PROGRESS,
            ComplaintAssignment.STATUS_COMPLETED,
            ComplaintAssignment.STATUS_REJECTED,
        ]
        counts = {s: base.filter_by(status=s).count() for s in statuses}
        total = base.count()
        active = base.filter(
            ComplaintAssignment.status.in_([
                ComplaintAssignment.STATUS_ASSIGNED,
                ComplaintAssignment.STATUS_ACCEPTED,
                ComplaintAssignment.STATUS_IN_PROGRESS,
            ])
        ).count()

        recent = (
            base.order_by(ComplaintAssignment.assigned_at.desc()).limit(5).all()
        )

        return {
            "total_assignments": total,
            "active_assignments": active,
            "by_status": counts,
            "recent_assignments": [self._serialize(a, full=True) for a in recent],
        }

    # ── Helpers ───────────────────────────────────────────────────────────

    def _get_owned(
        self, assignment_id: int, worker_id: int
    ) -> ComplaintAssignment:
        """Fetch an assignment and verify ownership.

        Raises:
            ValueError: If not found or not owned by this worker.
        """
        assignment = ComplaintAssignment.query.get(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found.")
        if assignment.worker_id != worker_id:
            raise ValueError(
                "You do not have permission to access this assignment."
            )
        return assignment

    @staticmethod
    def _ensure_complaint_actionable(complaint: Complaint) -> None:
        """Guard against acting on an assignment whose complaint has already
        moved past the field worker's control (e.g. an administrator rejected
        or closed it, or the citizen cancelled it, while the assignment was
        still active).

        Raises:
            ValueError: If the complaint is in a terminal state.
        """
        if not complaint:
            return
        terminal_statuses = (
            Complaint.STATUS_REJECTED,
            Complaint.STATUS_CANCELLED,
            Complaint.STATUS_RESOLVED,
            Complaint.STATUS_CLOSED,
        )
        if complaint.status in terminal_statuses:
            raise ValueError(
                f"This complaint has been '{complaint.status}' and no longer accepts "
                "field worker updates."
            )

    @staticmethod
    def _serialize(assignment: ComplaintAssignment, full: bool = False) -> dict:
        """Serialise a ComplaintAssignment."""
        data = {
            "id": assignment.id,
            "complaint_id": assignment.complaint_id,
            "worker_id": assignment.worker_id,
            "assigned_by_id": assignment.assigned_by_id,
            "status": assignment.status,
            "notes": assignment.notes,
            "evidence_url": assignment.evidence_url,
            "assigned_at": assignment.assigned_at.isoformat(),
            "expected_completion_at": (
                assignment.expected_completion_at.isoformat()
                if assignment.expected_completion_at else None
            ),
            "updated_at": (
                assignment.updated_at.isoformat()
                if assignment.updated_at else None
            ),
            "accepted_at": (
                assignment.accepted_at.isoformat()
                if assignment.accepted_at else None
            ),
            "completed_at": (
                assignment.completed_at.isoformat()
                if assignment.completed_at else None
            ),
        }
        if full and assignment.complaint:
            c = assignment.complaint
            data["complaint"] = {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "category": c.category,
                "status": c.status,
                "priority": c.priority,
                "address": c.address,
                "latitude": c.latitude,
                "longitude": c.longitude,
                "image_url": c.image_url,
                "pincode": c.pincode,
                "city_name": c.city.name if c.city else None,
                "citizen_name": c.citizen.full_name if c.citizen else None,
                "citizen_phone": c.citizen.phone if c.citizen else None,
                "created_at": c.created_at.isoformat(),
            }
        return data
