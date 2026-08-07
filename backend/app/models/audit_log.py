"""
AuditLog model — immutable system audit trail.
"""

from datetime import datetime, timezone
from app.extensions import db
from app.utils.db_types import UTCDateTime


class AuditLog(db.Model):
    """Records significant system actions for auditing purposes."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=True)
    resource_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(UTCDateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by user={self.user_id}>"
