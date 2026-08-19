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
    city_id = fields.Int(dump_only=True, allow_none=True)
    pincode = fields.Str(dump_only=True, allow_none=True)
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
        validate=validate.OneOf(["pothole"]),
    )
    priority = fields.Str(
        validate=validate.OneOf(["low", "medium", "high", "urgent"]),
        required=False,
    )
    latitude = fields.Float(allow_none=True)
    longitude = fields.Float(allow_none=True)
    address = fields.Str(validate=validate.Length(max=500), allow_none=True)
    image_url = fields.Str(required=True, validate=validate.Length(max=500))
    city_id = fields.Int(allow_none=True)
    pincode = fields.Str(validate=validate.Regexp(r"^\d{6}$"), allow_none=True)


class ComplaintUpdateSchema(Schema):
    """Schema for citizen updating their own pending complaint.

    Citizens can only change descriptive fields — status and priority
    are controlled exclusively by the administrator.
    """

    title = fields.Str(validate=validate.Length(min=5, max=200))
    description = fields.Str(validate=validate.Length(min=10))
    category = fields.Str(
        validate=validate.OneOf(
            ["pothole"]
        )
    )
    address = fields.Str(validate=validate.Length(max=500), allow_none=True)
    image_url = fields.Str(validate=validate.Length(max=500), allow_none=True)
    latitude = fields.Float(allow_none=True)
    longitude = fields.Float(allow_none=True)


class AdminComplaintUpdateSchema(Schema):
    """Schema for admin updating a complaint's status and/or priority."""

    status = fields.Str(
        validate=validate.OneOf(
            ["pending", "assigned", "in_progress", "resolved", "closed", "rejected"]
        )
    )
    priority = fields.Str(validate=validate.OneOf(["low", "medium", "high", "urgent"]))
    rejection_reason = fields.Str(validate=validate.Length(max=1000), allow_none=True)


class MarkDuplicateSchema(Schema):
    """Schema for admin linking a complaint as a duplicate of another one."""

    duplicate_of_id = fields.Int(required=True)
    reason = fields.Str(validate=validate.Length(max=500), allow_none=True)
