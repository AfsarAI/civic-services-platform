"""
User model — platform users with role-based access.
"""

from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(db.Model):
    """Represents a platform user (Citizen, Administrator, or Field Worker)."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    role = db.relationship("Role", back_populates="users")
    complaints = db.relationship(
        "Complaint", foreign_keys="Complaint.citizen_id",
        back_populates="citizen", lazy="dynamic"
    )
    assignments = db.relationship(
        "ComplaintAssignment", foreign_keys="ComplaintAssignment.worker_id",
        back_populates="worker", lazy="dynamic"
    )
    notifications = db.relationship("Notification", back_populates="user", lazy="dynamic")
    feedback = db.relationship("Feedback", back_populates="citizen", lazy="dynamic")

    def set_password(self, password: str) -> None:
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the user's password."""
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<User {self.username}>"
