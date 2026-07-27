"""
Citizen service — business logic for citizen-facing operations.
"""

from app.api.notifications.service import NotificationService
from app.extensions import db
from app.models.city import City
from app.models.city_pincode import CityPincode
from app.models.complaint import Complaint
from app.models.complaint_assignment import ComplaintAssignment
from app.models.feedback import Feedback
from app.models.notification import Notification
from app.models.user import User
from app.services.system_settings_service import SystemSettingsService


class CitizenService:
    """Handles complaint submission, tracking, editing, and feedback."""

    def __init__(self):
        self.notifications = NotificationService()

    # ── List complaints ───────────────────────────────────────────────────

    def get_my_complaints(
        self,
        citizen_id: int,
        page: int = 1,
        per_page: int = 20,
        status: str = None,
    ) -> dict:
        """Return paginated complaints belonging to this citizen.

        Args:
            citizen_id: ID of the authenticated citizen.
            page: 1-based page number.
            per_page: Page size (capped at 100).
            status: Optional status filter.

        Returns:
            Dict suitable for ``paginated_response``.
        """
        per_page = min(per_page, 100)
        query = Complaint.query.filter_by(citizen_id=citizen_id)

        if status:
            if status not in Complaint.VALID_STATUSES:
                raise ValueError(f"Invalid status '{status}'.")
            query = query.filter_by(status=status)

        query = query.order_by(Complaint.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": [self._serialize(c) for c in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
        }

    # ── Submit complaint ──────────────────────────────────────────────────

    def submit_complaint(self, citizen_id: int, data: dict) -> dict:
        """Create a new complaint in ``pending`` status.

        Args:
            citizen_id: ID of the authenticated citizen.
            data: Validated dict from ``ComplaintCreateSchema``.

        Returns:
            Dict with ``complaint`` key.
        """
        citizen = User.query.get(citizen_id)
        if not citizen:
            raise ValueError("Citizen account not found.")

        city_id, pincode = self._resolve_complaint_city(citizen, data)

        complaint = Complaint(
            citizen_id=citizen_id,
            title=data["title"],
            description=data["description"],
            category=Complaint.CATEGORY_POTHOLE,
            priority=data.get("priority") or SystemSettingsService.get_settings().default_complaint_priority,
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            address=data.get("address"),
            image_url=data.get("image_url"),
            city_id=city_id,
            pincode=pincode,
            status=Complaint.STATUS_PENDING,
        )
        db.session.add(complaint)
        db.session.commit()
        if SystemSettingsService.notifications_enabled():
            self.notifications.send_notification(
                user_id=citizen_id,
                title="Complaint submitted",
                message=(
                    f"Your complaint #{complaint.id} '{complaint.title}' has been submitted "
                    "successfully and is pending review."
                ),
                notification_type=Notification.TYPE_COMPLAINT_SUBMITTED,
                related_complaint_id=complaint.id,
            )
        return {"complaint": self._serialize(complaint)}

    # ── Get one complaint ─────────────────────────────────────────────────

    def get_complaint(self, complaint_id: int, citizen_id: int) -> dict:
        """Return a single complaint owned by the citizen.

        Raises:
            ValueError: If not found or does not belong to this citizen.
        """
        complaint = self._get_owned(complaint_id, citizen_id)
        return {"complaint": self._serialize(complaint)}

    # ── Update complaint ──────────────────────────────────────────────────

    def update_complaint(
        self, complaint_id: int, citizen_id: int, data: dict
    ) -> dict:
        """Update a pending complaint (only allowed before assignment).

        Raises:
            ValueError: If not found, not owned, or no longer pending.
        """
        complaint = self._get_owned(complaint_id, citizen_id)

        if complaint.status != Complaint.STATUS_PENDING:
            raise ValueError(
                "Only pending complaints can be edited. "
                f"Current status: '{complaint.status}'."
            )

        for field in ("title", "description", "address", "image_url",
                      "latitude", "longitude"):
            if field in data and data[field] is not None:
                setattr(complaint, field, data[field])

        db.session.commit()
        return {"complaint": self._serialize(complaint)}

    # ── Cancel complaint ──────────────────────────────────────────────────

    def cancel_complaint(self, complaint_id: int, citizen_id: int) -> dict:
        """Cancel a pending complaint (TPS-75).

        The complaint record is preserved with status ``cancelled`` (not
        deleted) so it remains visible in the citizen's history but is
        never considered for assignment or repair again.

        Raises:
            ValueError: If not found, not owned, or already assigned/in-progress.
        """
        complaint = self._get_owned(complaint_id, citizen_id)

        if complaint.status != Complaint.STATUS_PENDING:
            raise ValueError(
                "Only pending complaints can be cancelled. "
                f"Current status: '{complaint.status}'."
            )

        complaint.status = Complaint.STATUS_CANCELLED
        db.session.commit()
        return {"complaint": self._serialize(complaint)}

    # ── Submit feedback ───────────────────────────────────────────────────

    def submit_feedback(
        self, complaint_id: int, citizen_id: int, data: dict
    ) -> dict:
        """Submit a rating and optional comment on a resolved complaint.

        Only allowed when complaint status is ``resolved`` or ``closed``.
        One feedback per complaint (enforced by unique constraint).

        Raises:
            ValueError: Business rule violations.
        """
        # Ensure complaint is resolved or closed before accepting feedback and rating.
        complaint = self._get_owned(complaint_id, citizen_id)

        if complaint.status not in (
            Complaint.STATUS_RESOLVED, Complaint.STATUS_CLOSED
        ):
            raise ValueError(
                "Feedback can only be submitted for resolved or closed complaints. "
                f"Current status: '{complaint.status}'."
            )

        if complaint.feedback:
            raise ValueError("Feedback has already been submitted for this complaint.")

        feedback = Feedback(
            complaint_id=complaint_id,
            citizen_id=citizen_id,
            rating=data["rating"],
            comment=data.get("comment"),
        )
        db.session.add(feedback)
        db.session.commit()

        return {"feedback": self._serialize_feedback(feedback)}

    # ── Dashboard summary ─────────────────────────────────────────────────

    def get_dashboard_summary(self, citizen_id: int) -> dict:
        """Return complaint counts grouped by status for the citizen dashboard."""
        base = Complaint.query.filter_by(citizen_id=citizen_id)

        counts = {s: 0 for s in Complaint.VALID_STATUSES}
        for status in Complaint.VALID_STATUSES:
            counts[status] = base.filter_by(status=status).count()

        total = base.count()

        recent = (
            base.order_by(Complaint.created_at.desc()).limit(5).all()
        )

        return {
            "total_complaints": total,
            "by_status": counts,
            "recent_complaints": [self._serialize(c) for c in recent],
        }

    # ── Helpers ───────────────────────────────────────────────────────────

    def _get_owned(self, complaint_id: int, citizen_id: int) -> Complaint:
        """Fetch a complaint and verify ownership.

        Raises:
            ValueError: If not found or not owned by this citizen.
        """
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        if complaint.citizen_id != citizen_id:
            raise ValueError("You do not have permission to access this complaint.")
        return complaint

    @staticmethod
    def _serialize(complaint: Complaint) -> dict:
        """Safe public representation of a Complaint."""
        latest_assignment = (
            complaint.assignments.order_by(ComplaintAssignment.assigned_at.desc()).first()
        )
        return {
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
            "city_id": complaint.city_id,
            "city_name": complaint.city.name if complaint.city else None,
            "pincode": complaint.pincode,
            "citizen_id": complaint.citizen_id,
            "resolved_at": (
                complaint.resolved_at.isoformat() if complaint.resolved_at else None
            ),
            "created_at": complaint.created_at.isoformat(),
            "updated_at": complaint.updated_at.isoformat(),
            "feedback": (
                CitizenService._serialize_feedback(complaint.feedback)
                if complaint.feedback else None
            ),
            # Lets the citizen UI distinguish "repair work still ongoing" from
            # "field worker finished, awaiting administrator verification" even
            # though the complaint itself stays `in_progress` until resolved.
            "assignment_status": latest_assignment.status if latest_assignment else None,
            "repair_completed_at": (
                latest_assignment.completed_at.isoformat()
                if latest_assignment and latest_assignment.completed_at else None
            ),
        }

    @staticmethod
    def _serialize_feedback(feedback: Feedback) -> dict:
        """Safe public representation of Feedback."""
        return {
            "id": feedback.id,
            "complaint_id": feedback.complaint_id,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "created_at": feedback.created_at.isoformat(),
        }

    @staticmethod
    def _resolve_complaint_city(citizen: User, data: dict) -> tuple[int | None, str | None]:
        payload_pincode = data.get("pincode")
        payload_city_id = data.get("city_id")
        if payload_pincode:
            mappings = CityPincode.query.filter_by(pincode=payload_pincode, is_active=True).all()
            if not mappings:
                raise ValueError("No city mapping found for the provided pincode.")

            if payload_city_id is not None:
                if not any(mapping.city_id == payload_city_id for mapping in mappings):
                    raise ValueError("Selected city does not match the provided pincode.")
                return payload_city_id, payload_pincode

            unique_city_ids = sorted({mapping.city_id for mapping in mappings})
            if len(unique_city_ids) > 1:
                raise ValueError("Multiple cities found for this pincode. Please select a city.")
            return unique_city_ids[0], payload_pincode

        if payload_city_id is not None:
            city = City.query.get(payload_city_id)
            if not city or not city.is_active:
                raise ValueError("Selected city is not valid.")
            return payload_city_id, None

        if citizen.city_id and citizen.pincode:
            return citizen.city_id, citizen.pincode
        return citizen.city_id, citizen.pincode
