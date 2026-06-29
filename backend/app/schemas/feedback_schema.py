"""
Feedback schemas — serialisation and validation for Feedback objects.
"""

from marshmallow import Schema, fields, validate


class FeedbackSchema(Schema):
    """Schema for serialising Feedback objects (read)."""

    id = fields.Int(dump_only=True)
    complaint_id = fields.Int(dump_only=True)
    citizen_id = fields.Int(dump_only=True)
    rating = fields.Int(dump_only=True)
    comment = fields.Str(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)


class FeedbackCreateSchema(Schema):
    """Schema for submitting feedback."""

    complaint_id = fields.Int(required=True)
    rating = fields.Int(required=True, validate=validate.Range(min=1, max=5))
    comment = fields.Str(validate=validate.Length(max=1000), allow_none=True)
