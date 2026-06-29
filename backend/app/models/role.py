"""
Role model — defines user roles in the system.
"""

from datetime import datetime, timezone
from app.extensions import db


class Role(db.Model):
    """Represents a user role (Citizen, Administrator, Field Worker)."""

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    users = db.relationship("User", back_populates="role", lazy="dynamic")

    # Role name constants
    CITIZEN = "citizen"
    ADMINISTRATOR = "administrator"
    FIELD_WORKER = "field_worker"

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
