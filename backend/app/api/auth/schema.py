"""
Auth namespace — Marshmallow schemas (request/response validation).
"""

from marshmallow import Schema, fields, validate


class LoginRequestSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class RegisterRequestSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8), load_only=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    phone = fields.Str(allow_none=True)


class TokenResponseSchema(Schema):
    access_token = fields.Str(dump_only=True)
    refresh_token = fields.Str(dump_only=True)
    token_type = fields.Str(dump_only=True, dump_default="Bearer")
