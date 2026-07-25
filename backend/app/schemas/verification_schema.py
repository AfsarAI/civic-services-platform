"""Schemas for administrator repair-verification decisions."""

from marshmallow import Schema, fields, validate


class VerificationDecisionSchema(Schema):
    """Validate an administrator's repair verification decision."""

    decision = fields.Str(
        required=True,
        validate=validate.OneOf(["approved", "rework_requested"]),
    )
    remarks = fields.Str(
        allow_none=True,
        validate=validate.Length(max=2000),
    )
