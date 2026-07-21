"""User schemas - serialization and validation for user objects."""

from marshmallow import Schema, ValidationError, fields, pre_load, validate, validates, validates_schema

from app.schemas.validators import (
    normalize_email,
    normalize_optional_string,
    normalize_string,
    validate_password_strength,
    validate_phone_number,
    validate_pincode,
)


class UserSchema(Schema):
    """Schema for serializing user objects (read)."""

    id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)
    email = fields.Email(dump_only=True)
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    full_name = fields.Str(dump_only=True)
    phone = fields.Str(dump_only=True, allow_none=True)
    city_id = fields.Int(dump_only=True, allow_none=True)
    city_name = fields.Str(dump_only=True, allow_none=True)
    pincode = fields.Str(dump_only=True, allow_none=True)
    is_active = fields.Bool(dump_only=True)
    role_id = fields.Int(dump_only=True)
    role = fields.Str(dump_only=True)
    admin_level = fields.Str(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class UserCreateSchema(Schema):
    """Schema for creating a new user (write)."""

    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    phone = fields.Str(load_only=True, allow_none=True)
    city_id = fields.Int(load_only=True, allow_none=True)
    pincode = fields.Str(load_only=True, allow_none=True)
    role_id = fields.Int(required=True)

    @pre_load
    def normalize_fields(self, data: dict, **_) -> dict:
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
    def validate_phone(self, value: str | None) -> None:
        validate_phone_number(value)

    @validates("pincode")
    def validate_postal_code(self, value: str | None) -> None:
        validate_pincode(value)


class UserUpdateSchema(Schema):
    """Schema for updating an existing user."""

    first_name = fields.Str(validate=validate.Length(min=1, max=80))
    last_name = fields.Str(validate=validate.Length(min=1, max=80))
    phone = fields.Str(allow_none=True)
    city_id = fields.Int(allow_none=True)
    pincode = fields.Str(allow_none=True)
    is_active = fields.Bool()

    @pre_load
    def normalize_fields(self, data: dict, **_) -> dict:
        if "first_name" in data:
            data["first_name"] = normalize_string(data.get("first_name"))
        if "last_name" in data:
            data["last_name"] = normalize_string(data.get("last_name"))
        if "phone" in data:
            data["phone"] = normalize_optional_string(data.get("phone"))
        if "pincode" in data:
            data["pincode"] = normalize_optional_string(data.get("pincode"))
        return data

    @validates("phone")
    def validate_phone(self, value: str | None) -> None:
        validate_phone_number(value)

    @validates("pincode")
    def validate_postal_code(self, value: str | None) -> None:
        validate_pincode(value)


class MunicipalAdminCreateSchema(Schema):
    """Schema for creating a municipal administrator."""

    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    confirm_password = fields.Str(
        required=True,
        load_only=True,
        error_messages={"required": "Confirm password is required."},
    )
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    phone = fields.Str(load_default=None, allow_none=True)
    pincode = fields.Str(required=True)
    city_id = fields.Int(load_default=None, allow_none=True)
    city_name = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=120))
    city_state = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=120))

    @pre_load
    def normalize_fields(self, data: dict, **_) -> dict:
        data["email"] = normalize_email(data.get("email"))
        for field in ("username", "first_name", "last_name", "city_name", "city_state"):
            if field in data:
                data[field] = normalize_optional_string(data.get(field))
        data["phone"] = normalize_optional_string(data.get("phone"))
        data["pincode"] = normalize_optional_string(data.get("pincode"))
        return data

    @validates("password")
    def validate_password(self, value: str) -> None:
        validate_password_strength(value)

    @validates("phone")
    def validate_phone(self, value: str | None) -> None:
        validate_phone_number(value)

    @validates("pincode")
    def validate_postal_code(self, value: str | None) -> None:
        validate_pincode(value)

    @validates_schema
    def validate_password_match(self, data: dict, **_) -> None:
        if data.get("password") != data.get("confirm_password"):
            raise ValidationError({"confirm_password": ["Confirm password must match password."]})


class MunicipalAdminUpdateSchema(Schema):
    """Schema for updating a municipal administrator."""

    first_name = fields.Str(validate=validate.Length(min=1, max=80))
    last_name = fields.Str(validate=validate.Length(min=1, max=80))
    phone = fields.Str(allow_none=True)
    is_active = fields.Bool()
    pincode = fields.Str(allow_none=True)
    city_id = fields.Int(allow_none=True)
    city_name = fields.Str(allow_none=True, validate=validate.Length(max=120))
    city_state = fields.Str(allow_none=True, validate=validate.Length(max=120))

    @pre_load
    def normalize_fields(self, data: dict, **_) -> dict:
        for field in ("first_name", "last_name", "city_name", "city_state"):
            if field in data:
                data[field] = normalize_optional_string(data.get(field))
        if "phone" in data:
            data["phone"] = normalize_optional_string(data.get("phone"))
        if "pincode" in data:
            data["pincode"] = normalize_optional_string(data.get("pincode"))
        return data

    @validates("phone")
    def validate_phone(self, value: str | None) -> None:
        validate_phone_number(value)

    @validates("pincode")
    def validate_postal_code(self, value: str | None) -> None:
        validate_pincode(value)


class FieldWorkerCreateSchema(Schema):
    """Schema for a municipal administrator creating a field worker.

    The field worker's ``city_id`` is not accepted from the request — it is
    always derived from the creating municipal administrator's own city.
    """

    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    confirm_password = fields.Str(
        required=True,
        load_only=True,
        error_messages={"required": "Confirm password is required."},
    )
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    phone = fields.Str(load_default=None, allow_none=True)

    @pre_load
    def normalize_fields(self, data: dict, **_) -> dict:
        data["email"] = normalize_email(data.get("email"))
        for field in ("username", "first_name", "last_name"):
            data[field] = normalize_string(data.get(field))
        data["phone"] = normalize_optional_string(data.get("phone"))
        return data

    @validates("password")
    def validate_password(self, value: str) -> None:
        validate_password_strength(value)

    @validates("phone")
    def validate_phone(self, value: str | None) -> None:
        validate_phone_number(value)

    @validates_schema
    def validate_password_match(self, data: dict, **_) -> None:
        if data.get("password") != data.get("confirm_password"):
            raise ValidationError({"confirm_password": ["Confirm password must match password."]})


class FieldWorkerUpdateSchema(Schema):
    """Schema for a municipal administrator editing/activating/deactivating a field worker."""

    first_name = fields.Str(validate=validate.Length(min=1, max=80))
    last_name = fields.Str(validate=validate.Length(min=1, max=80))
    phone = fields.Str(allow_none=True)
    is_active = fields.Bool()

    @pre_load
    def normalize_fields(self, data: dict, **_) -> dict:
        for field in ("first_name", "last_name"):
            if field in data:
                data[field] = normalize_string(data.get(field))
        if "phone" in data:
            data["phone"] = normalize_optional_string(data.get("phone"))
        return data

    @validates("phone")
    def validate_phone(self, value: str | None) -> None:
        validate_phone_number(value)
