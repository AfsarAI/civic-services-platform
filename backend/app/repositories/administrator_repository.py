"""
Repository helpers for administrator hierarchy operations.
"""

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.city import City
from app.models.city_pincode import CityPincode
from app.models.role import Role
from app.models.user import User


class AdministratorRepository:
    """Encapsulates municipal-administrator persistence concerns."""

    @staticmethod
    def get_user_by_email(email: str) -> User | None:
        return (
            User.query
            .options(
                joinedload(User.role),
                joinedload(User.admin_profile).joinedload(AdministratorProfile.city),
            )
            .filter_by(email=email)
            .first()
        )

    @staticmethod
    def get_user_by_username(username: str) -> User | None:
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_role_by_name(name: str) -> Role | None:
        return Role.query.filter_by(name=name).first()

    @staticmethod
    def list_cities() -> list[City]:
        return City.query.order_by(City.name.asc()).all()

    @staticmethod
    def find_city_by_name(city_name: str, state: str | None = None) -> City | None:
        normalized_name = city_name.strip()
        query = City.query.filter(func.lower(City.name) == normalized_name.lower())
        if state is not None:
            query = query.filter(func.lower(func.coalesce(City.state, "")) == state.strip().lower())
        return query.first()

    @staticmethod
    def find_cities_by_pincode(pincode: str) -> list[CityPincode]:
        return (
            CityPincode.query
            .options(joinedload(CityPincode.city))
            .join(City, City.id == CityPincode.city_id)
            .filter(CityPincode.pincode == pincode, CityPincode.is_active.is_(True))
            .order_by(City.name.asc())
            .all()
        )

    @staticmethod
    def get_city_pincode_mapping(pincode: str, city_id: int) -> CityPincode | None:
        return CityPincode.query.filter_by(pincode=pincode, city_id=city_id, is_active=True).first()

    @staticmethod
    def upsert_city_pincode(
        pincode: str,
        city_id: int,
        area_name: str | None = None,
        district: str | None = None,
        state: str | None = None,
    ) -> CityPincode:
        existing = CityPincode.query.filter_by(
            pincode=pincode,
            city_id=city_id,
            area_name=area_name,
        ).first()
        if existing:
            existing.is_active = True
            if district and not existing.district:
                existing.district = district
            if state and not existing.state:
                existing.state = state
            db.session.flush()
            return existing

        mapping = CityPincode(
            pincode=pincode,
            city_id=city_id,
            area_name=area_name,
            district=district,
            state=state,
            is_active=True,
        )
        db.session.add(mapping)
        db.session.flush()
        return mapping

    @staticmethod
    def list_municipal_administrators(
        page: int = 1,
        per_page: int = 20,
        is_active: bool | None = None,
        city_name: str | None = None,
    ):
        query = (
            User.query
            .options(
                joinedload(User.role),
                joinedload(User.admin_profile).joinedload(AdministratorProfile.city),
            )
            .join(AdministratorProfile, AdministratorProfile.user_id == User.id)
            .filter(AdministratorProfile.admin_level == AdministratorProfile.MUNICIPAL)
        )

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        if city_name:
            query = query.join(City, City.id == AdministratorProfile.city_id)
            query = query.filter(City.name.ilike(f"%{city_name.strip()}%"))

        return query.order_by(User.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )

    @staticmethod
    def get_municipal_admin_user(user_id: int) -> User | None:
        user = (
            User.query
            .options(
                joinedload(User.role),
                joinedload(User.admin_profile).joinedload(AdministratorProfile.city),
            )
            .get(user_id)
        )
        if not user or not user.admin_profile or not user.is_municipal_admin:
            return None
        return user

    @staticmethod
    def create_city(name: str, state: str | None = None) -> City:
        city = City(name=name, state=state, is_active=True)
        db.session.add(city)
        db.session.flush()
        return city

    @staticmethod
    def create_user(**kwargs) -> User:
        user = User(**kwargs)
        db.session.add(user)
        return user

    @staticmethod
    def create_admin_profile(**kwargs) -> AdministratorProfile:
        profile = AdministratorProfile(**kwargs)
        db.session.add(profile)
        db.session.flush()
        return profile
