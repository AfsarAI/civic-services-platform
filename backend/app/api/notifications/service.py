"""
Notification service — business logic placeholder.
"""


class NotificationService:
    """Handles notification delivery and management."""

    def get_user_notifications(self, user_id: int, page: int, per_page: int) -> dict:
        """Retrieve paginated notifications for a user. TODO: implement."""
        raise NotImplementedError

    def get_notification(self, notification_id: int, user_id: int) -> dict:
        """Retrieve a specific notification. TODO: implement."""
        raise NotImplementedError

    def mark_as_read(self, notification_id: int, user_id: int) -> dict:
        """Mark a notification as read. TODO: implement."""
        raise NotImplementedError

    def mark_all_as_read(self, user_id: int) -> None:
        """Mark all user notifications as read. TODO: implement."""
        raise NotImplementedError

    def get_unread_count(self, user_id: int) -> int:
        """Return the count of unread notifications. TODO: implement."""
        raise NotImplementedError

    def send_notification(
        self, user_id: int, title: str, message: str,
        notification_type: str, related_complaint_id: int = None,
    ) -> dict:
        """Create and send a notification to a user. TODO: implement."""
        raise NotImplementedError
