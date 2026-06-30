"""
Authentication service — business logic for auth operations.
"""

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
)

from app.extensions import db
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
        if User.query.filter_by(email=data["email"]).first():
            raise ValueError("An account with this email already exists.")

        if User.query.filter_by(username=data["username"]).first():
            raise ValueError("This username is already taken.")

        citizen_role = Role.query.filter_by(name=Role.CITIZEN).first()
        if not citizen_role:
            raise RuntimeError("Citizen role not found. Run 'flask seed' first.")

        user = User(
            username=data["username"],
            email=data["email"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone=data.get("phone"),
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
        user = User.query.get(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or account inactive.")

        additional_claims = {
            "role": user.role.name,
            "email": user.email,
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
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found.")

        return {"user": self._serialize_user(user)}

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _serialize_user(user: User) -> dict:
        """Return a safe public representation of a User (no password hash)."""
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "phone": user.phone,
            "role": user.role.name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
