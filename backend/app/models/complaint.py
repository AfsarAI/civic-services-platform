"""
Complaint model — civic complaints submitted by citizens.
"""

from datetime import datetime, timezone
from app.extensions import db


class Complaint(db.Model):
    """Represents a civic complaint (e.g. pothole, broken streetlight)."""

    __tablename__ = "complaints"

    # Status constants
    STATUS_PENDING = "pending"
    STATUS_ASSIGNED = "assigned"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_RESOLVED = "resolved"
    STATUS_CLOSED = "closed"
    STATUS_REJECTED = "rejected"
    STATUS_CANCELLED = "cancelled"

    VALID_STATUSES = [
        STATUS_PENDING,
        STATUS_ASSIGNED,
        STATUS_IN_PROGRESS,
        STATUS_RESOLVED,
        STATUS_CLOSED,
        STATUS_REJECTED,
        STATUS_CANCELLED,
    ]

    # Category constants
    CATEGORY_POTHOLE = "pothole"
    CATEGORY_STREETLIGHT = "streetlight"
    CATEGORY_DRAINAGE = "drainage"
    CATEGORY_GARBAGE = "garbage"
    CATEGORY_ROAD_DAMAGE = "road_damage"
    CATEGORY_OTHER = "other"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, default=CATEGORY_OTHER)
    status = db.Column(db.String(30), nullable=False, default=STATUS_PENDING, index=True)
    priority = db.Column(db.String(20), nullable=False, default="medium")
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    address = db.Column(db.String(500), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=True, index=True)
    pincode = db.Column(db.String(6), nullable=True, index=True)
    citizen_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    citizen = db.relationship("User", foreign_keys=[citizen_id], back_populates="complaints")
    city = db.relationship("City", back_populates="complaint_records")
    assignments = db.relationship("ComplaintAssignment", back_populates="complaint", lazy="dynamic")
    feedback = db.relationship("Feedback", back_populates="complaint", uselist=False)

    def __repr__(self) -> str:
        return f"<Complaint {self.id}: {self.title[:30]}>"
