"""
Administrator service — business logic for admin-facing operations.
"""

from datetime import datetime, timezone

from app.extensions import db
from app.models.complaint import Complaint
from app.models.complaint_assignment import ComplaintAssignment
from app.models.role import Role
from app.models.user import User


class AdminService:
    """Handles complaint management, user management, and platform statistics."""

    # ── Complaints ────────────────────────────────────────────────────────

    def get_all_complaints(
        self,
        page: int = 1,
        per_page: int = 20,
        status: str = None,
        category: str = None,
        priority: str = None,
        citizen_id: int = None,
    ) -> dict:
        """Return paginated complaints, optionally filtered."""
        per_page = min(per_page, 100)
        query = Complaint.query

        if status:
            if status not in Complaint.VALID_STATUSES:
                raise ValueError(f"Invalid status '{status}'.")
            query = query.filter_by(status=status)
        if category:
            query = query.filter_by(category=category)
        if priority:
            query = query.filter_by(priority=priority)
        if citizen_id:
            query = query.filter_by(citizen_id=citizen_id)

        query = query.order_by(Complaint.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": [self._serialize_complaint(c) for c in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
        }

    def get_complaint(self, complaint_id: int) -> dict:
        """Return full complaint details including assignment and feedback.

        Raises:
            ValueError: If complaint not found.
        """
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        return {"complaint": self._serialize_complaint(complaint, full=True)}

    def update_complaint(self, complaint_id: int, data: dict) -> dict:
        """Update a complaint's status and/or priority.

        When status transitions to ``resolved``, sets ``resolved_at``.

        Raises:
            ValueError: If complaint not found or status value invalid.
        """
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")

        if "status" in data:
            complaint.status = data["status"]
            if data["status"] == Complaint.STATUS_RESOLVED and not complaint.resolved_at:
                complaint.resolved_at = datetime.now(timezone.utc)

        if "priority" in data:
            complaint.priority = data["priority"]

        db.session.commit()
        return {"complaint": self._serialize_complaint(complaint, full=True)}

    def assign_complaint(
        self, complaint_id: int, admin_id: int, data: dict
    ) -> dict:
        """Assign a complaint to a field worker.

        Creates a ComplaintAssignment record and sets complaint status to
        ``assigned``.  Allows re-assignment if already in ``assigned`` state
        (creates a new assignment row; the old one stays for audit).

        Raises:
            ValueError: Business rule violations.
        """
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")

        if complaint.status not in (
            Complaint.STATUS_PENDING, Complaint.STATUS_ASSIGNED
        ):
            raise ValueError(
                "Only pending or already-assigned complaints can be assigned. "
                f"Current status: '{complaint.status}'."
            )

        worker = User.query.get(data["worker_id"])
        if not worker:
            raise ValueError("Field worker not found.")

        worker_role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
        if not worker_role or worker.role_id != worker_role.id:
            raise ValueError("The specified user is not a field worker.")

        if not worker.is_active:
            raise ValueError("The specified field worker is inactive.")

        assignment = ComplaintAssignment(
            complaint_id=complaint_id,
            worker_id=data["worker_id"],
            assigned_by_id=admin_id,
            status=ComplaintAssignment.STATUS_ASSIGNED,
            notes=data.get("notes"),
        )
        db.session.add(assignment)
        complaint.status = Complaint.STATUS_ASSIGNED
        db.session.commit()

        return {
            "assignment": self._serialize_assignment(assignment),
            "complaint": self._serialize_complaint(complaint),
        }

    # ── Users ─────────────────────────────────────────────────────────────

    def get_all_users(
        self,
        page: int = 1,
        per_page: int = 20,
        role: str = None,
        is_active: bool = None,
    ) -> dict:
        """Return paginated users, optionally filtered by role or is_active."""
        per_page = min(per_page, 100)
        query = User.query

        if role:
            role_obj = Role.query.filter_by(name=role).first()
            if not role_obj:
                raise ValueError(f"Unknown role '{role}'.")
            query = query.filter_by(role_id=role_obj.id)

        if is_active is not None:
            query = query.filter_by(is_active=is_active)

        query = query.order_by(User.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": [self._serialize_user(u) for u in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
        }

    def get_user(self, user_id: int) -> dict:
        """Return user details.

        Raises:
            ValueError: If user not found.
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found.")
        return {"user": self._serialize_user(user)}

    def update_user(self, user_id: int, admin_id: int, data: dict) -> dict:
        """Update a user's profile fields or active status.

        Admins cannot deactivate their own account.

        Raises:
            ValueError: Business rule violations.
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found.")

        if "is_active" in data and not data["is_active"] and user_id == admin_id:
            raise ValueError("You cannot deactivate your own account.")

        for field in ("first_name", "last_name", "phone", "is_active"):
            if field in data:
                setattr(user, field, data[field])

        db.session.commit()
        return {"user": self._serialize_user(user)}

    def get_field_workers(self) -> dict:
        """Return all active field workers (for assignment dropdown)."""
        fw_role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
        if not fw_role:
            return {"field_workers": []}

        workers = (
            User.query
            .filter_by(role_id=fw_role.id, is_active=True)
            .order_by(User.first_name)
            .all()
        )
        return {"field_workers": [self._serialize_user(w) for w in workers]}

    # ── Dashboard ─────────────────────────────────────────────────────────

    def get_dashboard_summary(self) -> dict:
        """Return platform-wide complaint counts and recent activity."""
        counts = {s: 0 for s in Complaint.VALID_STATUSES}
        for status in Complaint.VALID_STATUSES:
            counts[status] = Complaint.query.filter_by(status=status).count()

        total = Complaint.query.count()
        open_count = Complaint.query.filter(
            Complaint.status.in_([
                Complaint.STATUS_PENDING,
                Complaint.STATUS_ASSIGNED,
                Complaint.STATUS_IN_PROGRESS,
            ])
        ).count()

        recent = (
            Complaint.query
            .order_by(Complaint.created_at.desc())
            .limit(10)
            .all()
        )

        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()

        return {
            "total_complaints": total,
            "open_complaints": open_count,
            "by_status": counts,
            "total_users": total_users,
            "active_users": active_users,
            "recent_complaints": [self._serialize_complaint(c) for c in recent],
        }

    # ── Serializers ───────────────────────────────────────────────────────

    @staticmethod
    def _serialize_complaint(complaint: Complaint, full: bool = False) -> dict:
        data = {
            "id": complaint.id,
            "title": complaint.title,
            "description": complaint.description,
            "category": complaint.category,
            "status": complaint.status,
            "priority": complaint.priority,
            "latitude": complaint.latitude,
            "longitude": complaint.longitude,
            "address": complaint.address,
            "image_url": complaint.image_url,
            "citizen_id": complaint.citizen_id,
            "resolved_at": (
                complaint.resolved_at.isoformat() if complaint.resolved_at else None
            ),
            "created_at": complaint.created_at.isoformat(),
            "updated_at": complaint.updated_at.isoformat(),
        }
        if full:
            data["citizen"] = (
                AdminService._serialize_user(complaint.citizen)
                if complaint.citizen else None
            )
            data["assignments"] = [
                AdminService._serialize_assignment(a)
                for a in complaint.assignments.order_by(
                    ComplaintAssignment.assigned_at.desc()
                )
            ]
            data["feedback"] = (
                AdminService._serialize_feedback(complaint.feedback)
                if complaint.feedback else None
            )
        return data

    @staticmethod
    def _serialize_user(user: User) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "phone": user.phone,
            "is_active": user.is_active,
            "role_id": user.role_id,
            "role": user.role.name if user.role else None,
            "created_at": user.created_at.isoformat(),
        }

    @staticmethod
    def _serialize_assignment(assignment: ComplaintAssignment) -> dict:
        return {
            "id": assignment.id,
            "complaint_id": assignment.complaint_id,
            "worker_id": assignment.worker_id,
            "assigned_by_id": assignment.assigned_by_id,
            "status": assignment.status,
            "notes": assignment.notes,
            "assigned_at": assignment.assigned_at.isoformat(),
            "accepted_at": (
                assignment.accepted_at.isoformat() if assignment.accepted_at else None
            ),
            "completed_at": (
                assignment.completed_at.isoformat() if assignment.completed_at else None
            ),
        }

    @staticmethod
    def _serialize_feedback(feedback) -> dict:
        return {
            "id": feedback.id,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "created_at": feedback.created_at.isoformat(),
        }
