"""
Auth namespace — Marshmallow schemas (request/response validation).
"""

import re

from marshmallow import Schema, ValidationError, fields, pre_load, validate, validates


# ---------------------------------------------------------------------------
# Shared validators
# ---------------------------------------------------------------------------

def _validate_password_strength(value: str) -> None:
    """Enforce password complexity: min 8 chars, 1 uppercase, 1 digit, 1 special."""
    if len(value) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", value):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"\d", value):
        raise ValidationError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_]", value):
        raise ValidationError(
            "Password must contain at least one special character (e.g. @, #, !)."
        )


# Accepts international E.164 format (+91...) or 10-digit Indian numbers,
# with optional spaces/hyphens between groups.
_PHONE_PATTERN = re.compile(
    r"^\+?(\d[\s\-]?){9,14}\d$"
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class LoginRequestSchema(Schema):
    email = fields.Email(required=True, error_messages={"required": "Email is required."})
    password = fields.Str(
        required=True,
        load_only=True,
        error_messages={"required": "Password is required."},
    )

    @pre_load
    def normalize_email(self, data: dict, **_) -> dict:
        if isinstance(data.get("email"), str):
            data["email"] = data["email"].strip().lower()
        return data


class RegisterRequestSchema(Schema):
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=80),
        error_messages={"required": "Username is required."},
    )
    email = fields.Email(
        required=True,
        error_messages={"required": "Email address is required."},
    )
    password = fields.Str(
        required=True,
        load_only=True,
        error_messages={"required": "Password is required."},
    )
    first_name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=80),
        error_messages={"required": "First name is required."},
    )
    last_name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=80),
        error_messages={"required": "Last name is required."},
    )
    phone = fields.Str(
        load_default=None,
        allow_none=True,
    )

    @pre_load
    def normalize_fields(self, data: dict, **_) -> dict:
        """Strip whitespace; lowercase email."""
        if isinstance(data.get("email"), str):
            data["email"] = data["email"].strip().lower()
        for field in ("username", "first_name", "last_name"):
            if isinstance(data.get(field), str):
                data[field] = data[field].strip()
        if isinstance(data.get("phone"), str):
            data["phone"] = data["phone"].strip() or None
        return data

    @validates("password")
    def validate_password(self, value: str) -> None:
        _validate_password_strength(value)

    @validates("phone")
    def validate_phone(self, value) -> None:
        if value is None:
            return
        if not _PHONE_PATTERN.match(value):
            raise ValidationError(
                "Enter a valid phone number (e.g. +91-9876543210 or 9876543210)."
            )

    @validates("first_name")
    def validate_first_name(self, value: str) -> None:
        if not value or not value.strip():
            raise ValidationError("First name cannot be blank.")

    @validates("last_name")
    def validate_last_name(self, value: str) -> None:
        if not value or not value.strip():
            raise ValidationError("Last name cannot be blank.")


class TokenResponseSchema(Schema):
    access_token = fields.Str(dump_only=True)
    refresh_token = fields.Str(dump_only=True)
    token_type = fields.Str(dump_only=True, dump_default="Bearer")
