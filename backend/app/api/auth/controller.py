"""
Authentication controller — register, login, refresh, logout, me.

All endpoints return the standard envelope:
    { "success": bool, "message": str, "data": dict|null, "errors": dict|null }
"""

import os
from uuid import uuid4

from flask import current_app, request, send_from_directory
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)
from werkzeug.utils import secure_filename

from app.api.auth.schema import (
    ChangePasswordSchema,
    LoginRequestSchema,
    ProfileUpdateSchema,
    RegisterRequestSchema,
)
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
        "pincode": fields.String(required=True, example="226001"),
        "city_id": fields.Integer(example=42),
    },
)

_login_model = ns.model(
    "LoginRequest",
    {
        "email": fields.String(required=True, example="john@example.com"),
        "password": fields.String(required=True, example="Secret@123"),
    },
)

_profile_update_model = ns.model(
    "ProfileUpdateRequest",
    {
        "first_name": fields.String(required=True, example="John"),
        "last_name": fields.String(required=True, example="Doe"),
        "phone": fields.String(example="+91-9876543210"),
    },
)

_change_password_model = ns.model(
    "ChangePasswordRequest",
    {
        "current_password": fields.String(required=True, example="OldSecret@123"),
        "new_password": fields.String(required=True, example="NewSecret@456"),
        "confirm_password": fields.String(required=True, example="NewSecret@456"),
    },
)


def _avatar_media_dir() -> str:
    directory = os.path.join(current_app.instance_path, "uploads", "avatars")
    os.makedirs(directory, exist_ok=True)
    return directory


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

    @ns.expect(_profile_update_model)
    @ns.response(200, "Profile updated", _envelope)
    @ns.response(422, "Validation error", _envelope)
    @jwt_required()
    @validate_body(ProfileUpdateSchema)
    def put(self, body):
        """Update the authenticated user's own profile (no username/email/role change)."""
        user_id = int(get_jwt_identity())
        try:
            data = _svc.update_profile(user_id, body)
            return success_response(data, "Profile updated successfully.")
        except ValueError as exc:
            return error_response(str(exc), status_code=404)


@ns.route("/change-password")
class ChangePasswordResource(Resource):
    @ns.expect(_change_password_model)
    @ns.response(200, "Password changed", _envelope)
    @ns.response(400, "Current password incorrect", _envelope)
    @ns.response(422, "Validation error", _envelope)
    @jwt_required()
    @validate_body(ChangePasswordSchema)
    def post(self, body):
        """Change the authenticated user's own password."""
        user_id = int(get_jwt_identity())
        try:
            _svc.change_password(user_id, body)
            return success_response(None, "Password changed successfully.")
        except ValueError as exc:
            return error_response(str(exc), status_code=400)


@ns.route("/me/avatar")
class CurrentUserAvatarUploadResource(Resource):
    @ns.response(200, "Avatar uploaded", _envelope)
    @ns.response(400, "Invalid photo upload", _envelope)
    @jwt_required()
    def post(self):
        """Upload and set the authenticated user's profile photo."""
        photo = request.files.get("photo")
        if not photo or not photo.filename:
            return error_response("A photo file is required.", status_code=400)

        if not (photo.mimetype or "").startswith("image/"):
            return error_response("Please upload a valid image file.", status_code=400)

        original_name = secure_filename(photo.filename)
        _, extension = os.path.splitext(original_name)
        extension = extension.lower() if extension else ".jpg"
        filename = f"{uuid4().hex}{extension}"
        file_path = os.path.join(_avatar_media_dir(), filename)
        photo.save(file_path)

        avatar_url = f"/api/v1/auth/me/avatar/{filename}"
        user_id = int(get_jwt_identity())
        try:
            data = _svc.update_avatar(user_id, avatar_url)
            return success_response(data, "Profile photo updated successfully.")
        except ValueError as exc:
            return error_response(str(exc), status_code=404)


@ns.route("/me/avatar/<string:filename>")
@ns.param("filename", "Uploaded avatar filename")
class CurrentUserAvatarResource(Resource):
    @ns.response(200, "Avatar photo")
    def get(self, filename):
        """Serve an uploaded profile photo."""
        return send_from_directory(_avatar_media_dir(), filename)
