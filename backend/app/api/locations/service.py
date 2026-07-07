"""
Locations service — pincode and city lookup helpers for onboarding flows.
"""

import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.models.complaint import Complaint
from app.models.city import City
from app.models.city_pincode import CityPincode
from app.models.role import Role
from app.models.user import User


class LocationService:
    """Handles pincode and city lookup from database-backed master data."""

    @staticmethod
    def lookup_pincode(pincode: str) -> dict:
        normalized = (pincode or "").strip()
        mappings = (
            CityPincode.query
            .join(City, City.id == CityPincode.city_id)
            .filter(CityPincode.pincode == normalized, CityPincode.is_active.is_(True))
            .order_by(City.name.asc())
            .all()
        )

        grouped = {}
        for mapping in mappings:
            city = mapping.city
            if city.id not in grouped:
                grouped[city.id] = {
                    "city_id": city.id,
                    "city_name": city.name,
                    "state": city.state,
                    "areas": set(),
                    "districts": set(),
                }
            if mapping.area_name:
                grouped[city.id]["areas"].add(mapping.area_name)
            if mapping.district:
                grouped[city.id]["districts"].add(mapping.district)

        cities = []
        for item in grouped.values():
            cities.append(
                {
                    "city_id": item["city_id"],
                    "city_name": item["city_name"],
                    "state": item["state"],
                    "areas": sorted(item["areas"]),
                    "districts": sorted(item["districts"]),
                }
            )

        return {
            "pincode": normalized,
            "cities": cities,
            "match_count": len(cities),
        }

    @staticmethod
    def search_cities(query: str | None, limit: int = 10) -> dict:
        q = (query or "").strip()
        limit = max(1, min(limit, 50))

        city_query = City.query.filter(City.is_active.is_(True))
        if q:
            like_term = f"%{q}%"
            city_query = city_query.filter(City.name.ilike(like_term))

        cities = city_query.order_by(City.name.asc()).limit(limit).all()

        return {
            "items": [
                {
                    "id": city.id,
                    "name": city.name,
                    "state": city.state,
                }
                for city in cities
            ],
            "count": len(cities),
        }

    @staticmethod
    def search_pincode_prefix(prefix: str | None, limit: int = 10) -> dict:
        """Return pincode suggestions enriched with area/district/city details."""
        normalized = (prefix or "").strip()
        limit = max(1, min(limit, 50))

        if len(normalized) < 2 or not normalized.isdigit():
            return {
                "prefix": normalized,
                "items": [],
                "count": 0,
            }

        mappings = (
            CityPincode.query
            .join(City, City.id == CityPincode.city_id)
            .filter(
                CityPincode.is_active.is_(True),
                CityPincode.pincode.like(f"{normalized}%"),
            )
            .order_by(
                CityPincode.pincode.asc(),
                City.name.asc(),
                CityPincode.area_name.asc(),
            )
            .limit(limit)
            .all()
        )

        return {
            "prefix": normalized,
            "items": [
                {
                    "pincode": mapping.pincode,
                    "city_id": mapping.city_id,
                    "city_name": mapping.city.name if mapping.city else None,
                    "area_name": mapping.area_name,
                    "district": mapping.district,
                    "state": mapping.state or (mapping.city.state if mapping.city else None),
                }
                for mapping in mappings
            ],
            "count": len(mappings),
        }

    @staticmethod
    def get_public_overview() -> dict:
        """Aggregate public metrics for the landing page."""
        total_users = (
            User.query
            .join(Role, Role.id == User.role_id)
            .filter(Role.name == Role.CITIZEN)
            .count()
        )
        total_complaints = Complaint.query.count()

        open_complaints = Complaint.query.filter(
            Complaint.status.in_(
                [
                    Complaint.STATUS_PENDING,
                    Complaint.STATUS_ASSIGNED,
                    Complaint.STATUS_IN_PROGRESS,
                ]
            )
        ).count()

        resolved_complaints = Complaint.query.filter(
            Complaint.status.in_([Complaint.STATUS_RESOLVED, Complaint.STATUS_CLOSED])
        ).count()

        pincode_coverage = db_count_distinct(
            CityPincode.pincode,
            CityPincode.is_active.is_(True),
        )
        city_coverage = db_count_distinct(
            CityPincode.city_id,
            CityPincode.is_active.is_(True),
        )

        return {
            "registered_users": total_users,
            "open_complaints": open_complaints,
            "resolved_complaints": resolved_complaints,
            "total_complaints": total_complaints,
            "pincode_coverage": pincode_coverage,
            "city_coverage": city_coverage,
        }

    @staticmethod
    def reverse_geocode(latitude: float, longitude: float) -> dict:
        """Resolve coordinates to human-readable location and known city mapping."""
        if not is_valid_coordinate(latitude, longitude):
            raise ValueError("Latitude/longitude must be valid coordinate values.")

        payload = fetch_reverse_geocode_payload(latitude, longitude)
        if not payload:
            raise ValueError("Could not resolve location for the selected map pin.")

        address_block = payload.get("address") or {}
        pincode = normalize_pincode(address_block.get("postcode"))
        city_name = (
            address_block.get("city")
            or address_block.get("town")
            or address_block.get("municipality")
            or address_block.get("village")
        )

        district = address_block.get("state_district") or address_block.get("county")
        state = address_block.get("state")
        area = (
            address_block.get("suburb")
            or address_block.get("neighbourhood")
            or address_block.get("hamlet")
            or address_block.get("quarter")
        )

        city_options = []
        city_id = None
        if pincode:
            lookup = LocationService.lookup_pincode(pincode)
            city_options = lookup.get("cities", [])
            city_id = choose_best_city_id(city_options, city_name, state)

        return {
            "latitude": latitude,
            "longitude": longitude,
            "address": payload.get("display_name"),
            "area": area,
            "district": district,
            "state": state,
            "pincode": pincode,
            "city_name": city_name,
            "city_id": city_id,
            "city_options": city_options,
            "match_count": len(city_options),
            "source": "nominatim",
        }

    @staticmethod
    def get_public_complaint_pins(limit: int = 500) -> dict:
        """Return public complaint markers based on recorded coordinates."""
        limit = max(1, min(limit, 1000))

        complaints = (
            Complaint.query
            .options(joinedload(Complaint.city))
            .filter(
                Complaint.latitude.isnot(None),
                Complaint.longitude.isnot(None),
            )
            .order_by(Complaint.created_at.desc())
            .limit(limit)
            .all()
        )

        items = []
        for complaint in complaints:
            if not is_valid_coordinate(complaint.latitude, complaint.longitude):
                continue
            items.append(
                {
                    "id": complaint.id,
                    "title": complaint.title,
                    "category": complaint.category,
                    "status": complaint.status,
                    "priority": complaint.priority,
                    "latitude": complaint.latitude,
                    "longitude": complaint.longitude,
                    "city_name": complaint.city.name if complaint.city else None,
                    "pincode": complaint.pincode,
                    "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
                }
            )

        return {
            "items": items,
            "count": len(items),
            "max_results": limit,
        }


def db_count_distinct(column, *filters) -> int:
    query = CityPincode.query
    if filters:
        query = query.filter(*filters)
    value = query.with_entities(func.count(func.distinct(column))).scalar()
    return int(value or 0)


def is_valid_coordinate(latitude: float | None, longitude: float | None) -> bool:
    if latitude is None or longitude is None:
        return False
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def fetch_reverse_geocode_payload(latitude: float, longitude: float) -> dict | None:
    params = urlencode(
        {
            "lat": f"{latitude:.8f}",
            "lon": f"{longitude:.8f}",
            "format": "jsonv2",
            "addressdetails": 1,
        }
    )
    request = Request(
        f"https://nominatim.openstreetmap.org/reverse?{params}",
        headers={"User-Agent": "CivicServicesPlatform/1.0"},
    )
    try:
        with urlopen(request, timeout=8) as response:
            body = response.read().decode("utf-8")
            payload = json.loads(body)
            return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def normalize_pincode(raw_postcode: str | None) -> str | None:
    if not raw_postcode:
        return None
    match = re.search(r"(\d{6})", str(raw_postcode))
    if not match:
        return None
    return match.group(1)


def choose_best_city_id(city_options: list[dict], city_name: str | None, state: str | None) -> int | None:
    if not city_options:
        return None
    if len(city_options) == 1:
        return city_options[0].get("city_id")

    city_name_norm = (city_name or "").strip().lower()
    state_norm = (state or "").strip().lower()

    for option in city_options:
        opt_name = str(option.get("city_name") or "").strip().lower()
        opt_state = str(option.get("state") or "").strip().lower()
        if city_name_norm and opt_name == city_name_norm:
            if not state_norm or not opt_state or opt_state == state_norm:
                return option.get("city_id")
    return None
