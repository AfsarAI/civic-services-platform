"""
City model — administrative city boundary for municipal administrators.
"""

from datetime import datetime, timezone

from app.extensions import db


class City(db.Model):
    """Represents a city managed inside the platform."""

    __tablename__ = "cities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    state = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    administrator_profiles = db.relationship(
        "AdministratorProfile",
        back_populates="city",
        lazy="dynamic",
    )
    users = db.relationship("User", back_populates="city", lazy="dynamic")
    complaint_records = db.relationship("Complaint", back_populates="city", lazy="dynamic")
    pincode_mappings = db.relationship("CityPincode", back_populates="city", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<City {self.name}>"
