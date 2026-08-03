"""
SystemSetting model — singleton row storing platform-wide configuration.
"""

from datetime import datetime, timezone
from app.extensions import db


class SystemSetting(db.Model):
    """Represents platform-wide configuration, managed by the System Administrator.

    Implemented as a singleton — the application always reads/writes the
    first (and only) row, lazily creating it with defaults if missing.
    """

    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(120), nullable=False, default="Civic Services Platform")
    support_email = db.Column(db.String(120), nullable=True)
    maintenance_mode = db.Column(db.Boolean, nullable=False, default=False)
    notify_on_status_change = db.Column(db.Boolean, nullable=False, default=True)
    default_complaint_priority = db.Column(db.String(20), nullable=False, default="medium")
    # Radius (in meters) used by DuplicateDetectionService to flag possible
    # duplicate pothole reports at both submission time and admin review.
    duplicate_detection_radius_meters = db.Column(db.Integer, nullable=False, default=50)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    updated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Relationships
    updated_by = db.relationship("User", foreign_keys=[updated_by_id])

    def __repr__(self) -> str:
        return f"<SystemSetting site_name={self.site_name!r}>"
