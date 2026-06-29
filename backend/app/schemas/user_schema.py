"""
User schemas — serialisation and validation for User objects.
"""

from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    """Schema for serialising User objects (read)."""

    id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)
    email = fields.Email(dump_only=True)
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    full_name = fields.Str(dump_only=True)
    phone = fields.Str(dump_only=True, allow_none=True)
    is_active = fields.Bool(dump_only=True)
    role_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class UserCreateSchema(Schema):
    """Schema for creating a new User (write)."""

    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8), load_only=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    phone = fields.Str(load_only=True, validate=validate.Length(max=20), allow_none=True)
    role_id = fields.Int(required=True)


class UserUpdateSchema(Schema):
    """Schema for updating an existing User."""

    first_name = fields.Str(validate=validate.Length(min=1, max=80))
    last_name = fields.Str(validate=validate.Length(min=1, max=80))
    phone = fields.Str(validate=validate.Length(max=20), allow_none=True)
    is_active = fields.Bool()
