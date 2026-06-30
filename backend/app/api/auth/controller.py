"""
Authentication controller — register, login, refresh, logout, me.

All endpoints return the standard envelope:
    { "success": bool, "message": str, "data": dict|null, "errors": dict|null }
"""

from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)

from app.api.auth.schema import LoginRequestSchema, RegisterRequestSchema
from app.api.auth.service import AuthService
from app.utils.decorators import validate_body
from app.utils.responses import success_response, error_response

ns = Namespace("auth", description="Authentication operations", path="/auth")
_svc = AuthService()

# -- Swagger response models (documentation only) --------------------------

_envelope = ns.model(
    "ApiEnvelope",
    {
        "success": fields.Boolean,
        "message": fields.String,
        "data": fields.Raw(description="Payload or null"),
        "errors": fields.Raw(description="Field-level errors or null"),
    },
)

_register_model = ns.model(
    "RegisterRequest",
    {
        "username": fields.String(required=True, example="john_citizen"),
        "email": fields.String(required=True, example="john@example.com"),
        "password": fields.String(required=True, example="Secret@123"),
        "first_name": fields.String(required=True, example="John"),
        "last_name": fields.String(required=True, example="Doe"),
        "phone": fields.String(example="+91-9876543210"),
    },
)

_login_model = ns.model(
    "LoginRequest",
    {
        "email": fields.String(required=True, example="john@example.com"),
        "password": fields.String(required=True, example="Secret@123"),
    },
)


# -- Endpoints --------------------------------------------------------------

@ns.route("/register")
class RegisterResource(Resource):
    @ns.expect(_register_model)
    @ns.response(201, "User registered successfully", _envelope)
    @ns.response(409, "Email or username already taken", _envelope)
    @ns.response(422, "Validation error", _envelope)
    @validate_body(RegisterRequestSchema)
    def post(self, body):
        """Register a new citizen account (TPS-64)."""
        try:
            data = _svc.register_user(body)
            return success_response(data, "Registration successful.", 201)
        except ValueError as exc:
            return error_response(str(exc), status_code=409)


@ns.route("/login")
class LoginResource(Resource):
    @ns.expect(_login_model)
    @ns.response(200, "Login successful", _envelope)
    @ns.response(401, "Invalid credentials", _envelope)
    @ns.response(422, "Validation error", _envelope)
    @validate_body(LoginRequestSchema)
    def post(self, body):
        """Authenticate a user and return JWT tokens (TPS-65, TPS-66, TPS-67)."""
        try:
            data = _svc.login(body["email"], body["password"])
            return success_response(data, "Login successful.")
        except ValueError as exc:
            return error_response(str(exc), status_code=401)


@ns.route("/refresh")
class RefreshResource(Resource):
    @ns.response(200, "Token refreshed", _envelope)
    @ns.response(401, "Invalid or expired refresh token", _envelope)
    @jwt_required(refresh=True)
    def post(self):
        """Refresh the JWT access token using a valid refresh token."""
        user_id = int(get_jwt_identity())
        try:
            data = _svc.refresh_token(user_id)
            return success_response(data, "Token refreshed.")
        except ValueError as exc:
            return error_response(str(exc), status_code=401)


@ns.route("/logout")
class LogoutResource(Resource):
    @ns.response(200, "Logged out successfully", _envelope)
    @ns.response(401, "Unauthorised", _envelope)
    @jwt_required()
    def post(self):
        """Invalidate the current JWT session.

        JWT tokens are stateless so the client must discard both tokens.
        A production system would add the JTI to a Redis blocklist here.
        """
        return success_response(None, "Logged out successfully.")


@ns.route("/me")
class CurrentUserResource(Resource):
    @ns.response(200, "Current user profile", _envelope)
    @ns.response(401, "Unauthorised", _envelope)
    @jwt_required()
    def get(self):
        """Get the currently authenticated user's profile."""
        user_id = int(get_jwt_identity())
        try:
            data = _svc.get_current_user(user_id)
            return success_response(data, "User profile retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=404)
