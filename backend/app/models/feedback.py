"""
Feedback model — citizen feedback on resolved complaints.
"""

from datetime import datetime, timezone
from app.extensions import db


class Feedback(db.Model):
    """Represents feedback submitted by a citizen on a resolved complaint."""

    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id"), nullable=False, unique=True)
    citizen_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)  # 1–5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    complaint = db.relationship("Complaint", back_populates="feedback")
    citizen = db.relationship("User", back_populates="feedback")

    def __repr__(self) -> str:
        return f"<Feedback complaint={self.complaint_id} rating={self.rating}>"
