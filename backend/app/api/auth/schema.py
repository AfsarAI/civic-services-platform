"""
Auth namespace — Marshmallow schemas (request/response validation).
"""

from marshmallow import Schema, ValidationError, fields, pre_load, validate, validates

from app.schemas.validators import (
    normalize_email,
    normalize_optional_string,
    normalize_string,
    validate_password_strength,
    validate_pincode,
    validate_phone_number,
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
        data["email"] = normalize_email(data.get("email"))
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
    pincode = fields.Str(
        required=True,
        error_messages={"required": "Pincode is required."},
    )
    city_id = fields.Int(load_default=None, allow_none=True)

    @pre_load
    def normalize_fields(self, data: dict, **_) -> dict:
        """Strip whitespace; lowercase email."""
        data["email"] = normalize_email(data.get("email"))
        for field in ("username", "first_name", "last_name"):
            data[field] = normalize_string(data.get(field))
        data["phone"] = normalize_optional_string(data.get("phone"))
        data["pincode"] = normalize_optional_string(data.get("pincode"))
        return data

    @validates("password")
    def validate_password(self, value: str) -> None:
        validate_password_strength(value)

    @validates("phone")
    def validate_phone(self, value) -> None:
        validate_phone_number(value)

    @validates("pincode")
    def validate_postal_code(self, value) -> None:
        validate_pincode(value)

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
