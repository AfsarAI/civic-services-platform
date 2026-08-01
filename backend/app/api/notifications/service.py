"""
Notification service — notification management and delivery.
"""

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.notification import Notification


class NotificationService:
    """Handles notification delivery and management for all user roles."""

    # ── Read ──────────────────────────────────────────────────────────────

    def get_user_notifications(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        unread_only: bool = False,
    ) -> dict:
        """Return paginated notifications for a user.

        Args:
            user_id: ID of the authenticated user.
            page: 1-based page number.
            per_page: Page size (capped at 100).
            unread_only: When True, only return unread notifications.
        """
        per_page = min(per_page, 100)
        query = Notification.query.filter_by(user_id=user_id)

        if unread_only:
            query = query.filter_by(is_read=False)

        query = query.order_by(Notification.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": [self._serialize(n) for n in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
        }

    def get_notification(self, notification_id: int, user_id: int) -> dict:
        """Return a single notification owned by the user.

        Raises:
            ValueError: If not found or not owned by this user.
        """
        notification = self._get_owned(notification_id, user_id)
        return {"notification": self._serialize(notification)}

    def get_unread_count(self, user_id: int) -> dict:
        """Return the count of unread notifications."""
        count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        return {"count": count}

    # ── Mark as read ──────────────────────────────────────────────────────

    def mark_as_read(self, notification_id: int, user_id: int) -> dict:
        """Mark a single notification as read.

        Idempotent — already-read notifications return success without error.

        Raises:
            ValueError: If not found or not owned by this user.
        """
        notification = self._get_owned(notification_id, user_id)

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            db.session.commit()

        return {"notification": self._serialize(notification)}

    def mark_all_as_read(self, user_id: int) -> dict:
        """Mark all notifications for a user as read."""
        now = datetime.now(timezone.utc)
        updated = (
            Notification.query
            .filter_by(user_id=user_id, is_read=False)
            .update({"is_read": True, "read_at": now})
        )
        db.session.commit()
        return {"marked_read": updated}

    # ── Internal: send notification ───────────────────────────────────────

    def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = Notification.TYPE_GENERAL,
        related_complaint_id: int = None,
        related_assignment_id: int = None,
        commit: bool = True,
    ) -> dict:
        """Create and persist a notification for a user.

        Called internally by other services after state-changing events
        (e.g. complaint submitted, status updated).

        ``commit=False`` stages and flushes the notification in the caller's
        transaction. Existing callers retain the original commit behavior.

        Returns the serialised notification dict.
        """
        # Assignment notifications are idempotent per assignment event.
        if (
            notification_type == Notification.TYPE_COMPLAINT_ASSIGNED
            and related_assignment_id is not None
        ):
            existing = Notification.query.filter_by(
                user_id=user_id,
                notification_type=notification_type,
                related_assignment_id=related_assignment_id,
            ).first()
            if existing:
                return self._serialize(existing)

        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            related_complaint_id=related_complaint_id,
            related_assignment_id=related_assignment_id,
        )
        db.session.add(notification)
        try:
            if commit:
                db.session.commit()
            else:
                db.session.flush()
        except IntegrityError:
            if not commit:
                raise
            db.session.rollback()
            if (
                notification_type == Notification.TYPE_COMPLAINT_ASSIGNED
                and related_assignment_id is not None
            ):
                existing = Notification.query.filter_by(
                    user_id=user_id,
                    notification_type=notification_type,
                    related_assignment_id=related_assignment_id,
                ).first()
                if existing:
                    return self._serialize(existing)
            raise
        return self._serialize(notification)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _get_owned(self, notification_id: int, user_id: int) -> Notification:
        """Fetch a notification and verify ownership.

        Raises:
            ValueError: If not found or not owned by this user.
        """
        notification = Notification.query.get(notification_id)
        if not notification:
            raise ValueError("Notification not found.")
        if notification.user_id != user_id:
            raise ValueError(
                "You do not have permission to access this notification."
            )
        return notification

    @staticmethod
    def _serialize(notification: Notification) -> dict:
        """Safe public representation of a Notification."""
        return {
            "id": notification.id,
            "user_id": notification.user_id,
            "title": notification.title,
            "message": notification.message,
            "notification_type": notification.notification_type,
            "is_read": notification.is_read,
            "related_complaint_id": notification.related_complaint_id,
            "related_assignment_id": notification.related_assignment_id,
            "created_at": notification.created_at.isoformat(),
            "read_at": (
                notification.read_at.isoformat() if notification.read_at else None
            ),
        }
