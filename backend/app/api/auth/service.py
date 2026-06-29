"""
Authentication service — business logic placeholder.
"""


class AuthService:
    """Handles authentication and token management."""

    def register_user(self, data: dict) -> dict:
        """Register a new user. TODO: implement."""
        raise NotImplementedError

    def login(self, email: str, password: str) -> dict:
        """Validate credentials and issue JWT tokens. TODO: implement."""
        raise NotImplementedError

    def refresh_token(self, refresh_token: str) -> dict:
        """Issue a new access token. TODO: implement."""
        raise NotImplementedError

    def logout(self, jti: str) -> None:
        """Revoke the JWT token. TODO: implement."""
        raise NotImplementedError

    def get_current_user(self, user_id: int) -> dict:
        """Retrieve the authenticated user's profile. TODO: implement."""
        raise NotImplementedError
