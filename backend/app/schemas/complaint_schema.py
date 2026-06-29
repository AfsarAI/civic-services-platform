"""
Complaint schemas — serialisation and validation for Complaint objects.
"""

from marshmallow import Schema, fields, validate


class ComplaintSchema(Schema):
    """Schema for serialising Complaint objects (read)."""

    id = fields.Int(dump_only=True)
    title = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    category = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    priority = fields.Str(dump_only=True)
    latitude = fields.Float(dump_only=True, allow_none=True)
    longitude = fields.Float(dump_only=True, allow_none=True)
    address = fields.Str(dump_only=True, allow_none=True)
    image_url = fields.Str(dump_only=True, allow_none=True)
    citizen_id = fields.Int(dump_only=True)
    resolved_at = fields.DateTime(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ComplaintCreateSchema(Schema):
    """Schema for creating a new Complaint."""

    title = fields.Str(required=True, validate=validate.Length(min=5, max=200))
    description = fields.Str(required=True, validate=validate.Length(min=10))
    category = fields.Str(
        required=True,
        validate=validate.OneOf(
            ["pothole", "streetlight", "drainage", "garbage", "road_damage", "other"]
        ),
    )
    priority = fields.Str(
        validate=validate.OneOf(["low", "medium", "high", "urgent"]),
        load_default="medium",
    )
    latitude = fields.Float(allow_none=True)
    longitude = fields.Float(allow_none=True)
    address = fields.Str(validate=validate.Length(max=500), allow_none=True)
    image_url = fields.Str(validate=validate.Length(max=500), allow_none=True)


class ComplaintUpdateSchema(Schema):
    """Schema for updating a Complaint's status or details."""

    status = fields.Str(
        validate=validate.OneOf(
            ["pending", "assigned", "in_progress", "resolved", "closed", "rejected"]
        )
    )
    priority = fields.Str(validate=validate.OneOf(["low", "medium", "high", "urgent"]))
    description = fields.Str(validate=validate.Length(min=10))
