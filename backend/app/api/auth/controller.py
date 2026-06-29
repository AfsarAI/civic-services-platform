"""
Authentication controller — login, register, refresh, logout.
"""

from flask import request
from flask_restx import Namespace, Resource, fields

ns = Namespace("auth", description="Authentication operations", path="/auth")

# ── Request / Response models ──────────────────────────────────────────────

login_model = ns.model(
    "LoginRequest",
    {
        "email": fields.String(required=True, description="User email"),
        "password": fields.String(required=True, description="User password"),
    },
)

register_model = ns.model(
    "RegisterRequest",
    {
        "username": fields.String(required=True),
        "email": fields.String(required=True),
        "password": fields.String(required=True),
        "first_name": fields.String(required=True),
        "last_name": fields.String(required=True),
        "phone": fields.String(),
    },
)

token_model = ns.model(
    "TokenResponse",
    {
        "success": fields.Boolean,
        "message": fields.String,
        "data": fields.Raw(description="Token data"),
    },
)


# ── Endpoints ──────────────────────────────────────────────────────────────

@ns.route("/register")
class RegisterResource(Resource):
    @ns.expect(register_model, validate=True)
    @ns.response(201, "User registered successfully")
    @ns.response(400, "Validation error")
    @ns.response(409, "Email or username already exists")
    def post(self):
        """Register a new citizen account."""
        # TODO: implement via AuthService
        return {"success": True, "message": "Registration endpoint — not yet implemented", "data": None}, 501


@ns.route("/login")
class LoginResource(Resource):
    @ns.expect(login_model, validate=True)
    @ns.response(200, "Login successful", token_model)
    @ns.response(401, "Invalid credentials")
    def post(self):
        """Authenticate a user and return JWT tokens."""
        # TODO: implement via AuthService
        return {"success": True, "message": "Login endpoint — not yet implemented", "data": None}, 501


@ns.route("/refresh")
class RefreshResource(Resource):
    @ns.response(200, "Token refreshed", token_model)
    @ns.response(401, "Invalid or expired refresh token")
    def post(self):
        """Refresh the JWT access token using a valid refresh token."""
        # TODO: implement via AuthService
        return {"success": True, "message": "Refresh endpoint — not yet implemented", "data": None}, 501


@ns.route("/logout")
class LogoutResource(Resource):
    @ns.response(200, "Logged out successfully")
    def post(self):
        """Invalidate the current JWT token."""
        # TODO: implement via AuthService
        return {"success": True, "message": "Logout endpoint — not yet implemented", "data": None}, 501


@ns.route("/me")
class CurrentUserResource(Resource):
    @ns.response(200, "Current user profile")
    @ns.response(401, "Unauthorised")
    def get(self):
        """Get the currently authenticated user's profile."""
        # TODO: implement via AuthService
        return {"success": True, "message": "Me endpoint — not yet implemented", "data": None}, 501
