"""
CityPincode model — maps a pincode to one or more city records.
"""

from datetime import datetime, timezone
from app.extensions import db


class CityPincode(db.Model):
    """Pincode mapping for city lookup and onboarding flows."""

    __tablename__ = "city_pincodes"

    id = db.Column(db.Integer, primary_key=True)
    pincode = db.Column(db.String(6), nullable=False, index=True)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False, index=True)
    area_name = db.Column(db.String(120), nullable=True)
    district = db.Column(db.String(120), nullable=True)
    state = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("pincode", "city_id", "area_name", name="uq_city_pincode_city_area"),
    )

    city = db.relationship("City", back_populates="pincode_mappings")

    def __repr__(self) -> str:
        return f"<CityPincode {self.pincode} city={self.city_id}>"
