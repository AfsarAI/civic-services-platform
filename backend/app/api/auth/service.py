"""
Authentication service — business logic for auth operations.
"""

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
)

from app.extensions import db
from app.models.city_pincode import CityPincode
from app.models.role import Role
from app.models.user import User


class AuthService:
    """Handles user registration, login, token management, and profile access."""

    # ── Registration ──────────────────────────────────────────────────────

    def register_user(self, data: dict) -> dict:
        """Register a new citizen account.

        Args:
            data: Validated dict from RegisterRequestSchema.

        Returns:
            Dict with ``user`` key on success.

        Raises:
            ValueError: If email or username is already taken.
        """
        email = data["email"].strip().lower()
        if User.query.filter_by(email=email).first():
            raise ValueError("An account with this email already exists.")

        if User.query.filter_by(username=data["username"]).first():
            raise ValueError("This username is already taken.")

        citizen_role = Role.query.filter_by(name=Role.CITIZEN).first()
        if not citizen_role:
            raise RuntimeError("Citizen role not found. Run 'flask seed' first.")

        user = User(
            username=data["username"],
            email=email,
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone=data.get("phone"),
            city_id=self._resolve_city_id(data["pincode"], data.get("city_id")),
            pincode=data.get("pincode"),
            role_id=citizen_role.id,
            is_active=True,
        )
        user.set_password(data["password"])

        db.session.add(user)
        db.session.commit()

        return {"user": self._serialize_user(user)}

    # ── Login ─────────────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> dict:
        """Validate credentials and issue JWT access + refresh tokens.

        Args:
            email: User's email address.
            password: Plain-text password to verify.

        Returns:
            Dict with ``access_token``, ``refresh_token``, and ``user``.

        Raises:
            ValueError: If credentials are invalid or account is inactive.
        """
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            raise ValueError("Invalid email or password.")

        if not user.is_active:
            raise ValueError("Your account has been deactivated. Contact support.")

        additional_claims = {
            "role": user.role.name,
            "email": user.email,
            "admin_level": user.admin_level,
            "city_id": self._jwt_city_id(user),
        }

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims,
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims=additional_claims,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "user": self._serialize_user(user),
        }

    # ── Token refresh ─────────────────────────────────────────────────────

    def refresh_token(self, user_id: int) -> dict:
        """Issue a new access token for an authenticated user.

        Args:
            user_id: The current user's ID (from JWT identity).

        Returns:
            Dict with new ``access_token``.

        Raises:
            ValueError: If the user no longer exists or is inactive.
        """
        user = db.session.get(User, user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or account inactive.")

        additional_claims = {
            "role": user.role.name,
            "email": user.email,
            "admin_level": user.admin_level,
            "city_id": self._jwt_city_id(user),
        }

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims,
        )

        return {"access_token": access_token, "token_type": "Bearer"}

    # ── Current user profile ──────────────────────────────────────────────

    def get_current_user(self, user_id: int) -> dict:
        """Retrieve the authenticated user's profile.

        Args:
            user_id: The current user's ID (from JWT identity).

        Returns:
            Dict with ``user`` key.

        Raises:
            ValueError: If the user does not exist.
        """
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")

        return {"user": self._serialize_user(user)}

    def update_profile(self, user_id: int, data: dict) -> dict:
        """Update the authenticated user's own profile fields.

        Username, email, and role are never editable through this method.

        Raises:
            ValueError: If the user does not exist.
        """
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")

        user.first_name = data["first_name"]
        user.last_name = data["last_name"]
        user.phone = data.get("phone")

        db.session.commit()
        return {"user": self._serialize_user(user)}

    def change_password(self, user_id: int, data: dict) -> None:
        """Change the authenticated user's own password.

        Raises:
            ValueError: If the user does not exist or the current password is wrong.
        """
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")

        if not user.check_password(data["current_password"]):
            raise ValueError("Current password is incorrect.")

        user.set_password(data["new_password"])
        db.session.commit()

    def update_avatar(self, user_id: int, avatar_url: str) -> dict:
        """Set the authenticated user's profile photo URL.

        Raises:
            ValueError: If the user does not exist.
        """
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")

        user.avatar_url = avatar_url
        db.session.commit()
        return {"user": self._serialize_user(user)}

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _serialize_user(user: User) -> dict:
        """Return a safe public representation of a User (no password hash)."""
        city_id = user.admin_city_id if user.is_administrator else user.city_id
        city_name = user.admin_city_name if user.is_administrator else (user.city.name if user.city else None)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "role": user.role.name,
            "admin_level": user.admin_level,
            "city_id": city_id,
            "city_name": city_name,
            "pincode": user.pincode,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    @staticmethod
    def _jwt_city_id(user: User) -> int | None:
        return user.admin_city_id if user.is_administrator else user.city_id

    @staticmethod
    def _resolve_city_id(pincode: str, city_id: int | None) -> int:
        mappings = CityPincode.query.filter_by(pincode=pincode, is_active=True).all()
        if not mappings:
            raise ValueError("No city mapping found for the provided pincode.")

        if city_id is not None:
            if not any(m.city_id == city_id for m in mappings):
                raise ValueError("Selected city does not match the provided pincode.")
            return city_id

        unique_city_ids = sorted({m.city_id for m in mappings})
        if len(unique_city_ids) > 1:
            raise ValueError("Multiple cities found for this pincode. Please select a city.")
        return unique_city_ids[0]
