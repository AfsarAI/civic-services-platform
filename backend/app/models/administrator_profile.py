"""
Administrator profile model — subtype metadata for administrator users.
"""

from datetime import datetime, timezone

from app.extensions import db


class AdministratorProfile(db.Model):
    """Represents the subtype and scope of an administrator user."""

    __tablename__ = "administrator_profiles"
    __table_args__ = (
        db.CheckConstraint(
            "("
            "admin_level = 'system' AND city_id IS NULL"
            ") OR ("
            "admin_level = 'municipal' AND city_id IS NOT NULL"
            ")",
            name="ck_admin_profiles_level_city_scope",
        ),
    )

    SYSTEM = "system"
    MUNICIPAL = "municipal"
    VALID_LEVELS = (SYSTEM, MUNICIPAL)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    admin_level = db.Column(db.String(20), nullable=False, index=True)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=True, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="admin_profile",
    )
    city = db.relationship("City", back_populates="administrator_profiles")
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    @property
    def is_system_admin(self) -> bool:
        return self.admin_level == self.SYSTEM

    @property
    def is_municipal_admin(self) -> bool:
        return self.admin_level == self.MUNICIPAL

    def __repr__(self) -> str:
        return f"<AdministratorProfile user_id={self.user_id} level={self.admin_level}>"
