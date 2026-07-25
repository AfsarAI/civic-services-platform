"""
ComplaintVerification model — administrator repair-review decisions.
"""

from datetime import datetime, timezone

from app.extensions import db


class ComplaintVerification(db.Model):
    """Immutable record of an administrator's repair verification decision."""

    __tablename__ = "complaint_verifications"
    __table_args__ = (
        db.UniqueConstraint(
            "assignment_id",
            "repair_completed_at",
            name="uq_verification_assignment_completion",
        ),
    )

    DECISION_APPROVED = "approved"
    DECISION_REWORK_REQUESTED = "rework_requested"
    VALID_DECISIONS = (DECISION_APPROVED, DECISION_REWORK_REQUESTED)

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.id"),
        nullable=False,
        index=True,
    )
    assignment_id = db.Column(
        db.Integer,
        db.ForeignKey("complaint_assignments.id"),
        nullable=False,
        index=True,
    )
    administrator_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    decision = db.Column(db.String(30), nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    repair_completed_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    complaint = db.relationship("Complaint", back_populates="verifications")
    assignment = db.relationship(
        "ComplaintAssignment",
        back_populates="verifications",
    )
    administrator = db.relationship("User", foreign_keys=[administrator_id])

    def __repr__(self) -> str:
        return (
            f"<ComplaintVerification complaint={self.complaint_id} "
            f"decision={self.decision}>"
        )
