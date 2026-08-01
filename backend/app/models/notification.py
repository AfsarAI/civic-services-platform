"""
Notification model — system notifications for users.
"""

from datetime import datetime, timezone
from app.extensions import db


class Notification(db.Model):
    """Represents a notification sent to a platform user."""

    __tablename__ = "notifications"

    TYPE_COMPLAINT_SUBMITTED = "complaint_submitted"
    TYPE_COMPLAINT_ASSIGNED = "complaint_assigned"
    TYPE_STATUS_UPDATE = "status_update"
    TYPE_COMPLAINT_RESOLVED = "complaint_resolved"
    TYPE_GENERAL = "general"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False, default=TYPE_GENERAL)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    related_complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id"), nullable=True)
    related_assignment_id = db.Column(
        db.Integer,
        db.ForeignKey("complaint_assignments.id"),
        nullable=True,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    read_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification {self.id} user={self.user_id}>"
