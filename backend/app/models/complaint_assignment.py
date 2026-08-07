"""
ComplaintAssignment model — assignment of complaints to field workers.
"""

from datetime import datetime, timezone
from app.extensions import db
from app.utils.db_types import UTCDateTime


class ComplaintAssignment(db.Model):
    """Tracks the assignment of a complaint to a field worker."""

    __tablename__ = "complaint_assignments"

    STATUS_ASSIGNED = "assigned"
    STATUS_ACCEPTED = "accepted"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_REJECTED = "rejected"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id"), nullable=False, index=True)
    worker_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(30), nullable=False, default=STATUS_ASSIGNED)
    notes = db.Column(db.Text, nullable=True)
    evidence_url = db.Column(db.String(500), nullable=True)
    assigned_at = db.Column(UTCDateTime, default=lambda: datetime.now(timezone.utc))
    expected_completion_at = db.Column(UTCDateTime, nullable=True)
    accepted_at = db.Column(UTCDateTime, nullable=True)
    completed_at = db.Column(UTCDateTime, nullable=True)
    updated_at = db.Column(
        UTCDateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    complaint = db.relationship("Complaint", back_populates="assignments")
    worker = db.relationship("User", foreign_keys=[worker_id], back_populates="assignments")
    assigned_by = db.relationship("User", foreign_keys=[assigned_by_id])
    verifications = db.relationship(
        "ComplaintVerification",
        back_populates="assignment",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Assignment complaint={self.complaint_id} worker={self.worker_id}>"
