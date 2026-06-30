"""
Assignment schemas — serialisation and validation for ComplaintAssignment objects.
"""

from marshmallow import Schema, fields, validate


class AssignmentSchema(Schema):
    """Schema for serialising ComplaintAssignment objects (read)."""

    id = fields.Int(dump_only=True)
    complaint_id = fields.Int(dump_only=True)
    worker_id = fields.Int(dump_only=True)
    assigned_by_id = fields.Int(dump_only=True)
    status = fields.Str(dump_only=True)
    notes = fields.Str(dump_only=True, allow_none=True)
    assigned_at = fields.DateTime(dump_only=True)
    accepted_at = fields.DateTime(dump_only=True, allow_none=True)
    completed_at = fields.DateTime(dump_only=True, allow_none=True)
    updated_at = fields.DateTime(dump_only=True)


class AssignmentCreateSchema(Schema):
    """Schema for creating a new assignment."""

    complaint_id = fields.Int(required=True)
    worker_id = fields.Int(required=True)
    notes = fields.Str(validate=validate.Length(max=1000), allow_none=True)


class AssignmentUpdateSchema(Schema):
    """Schema for updating an assignment status."""

    status = fields.Str(
        required=True,
        validate=validate.OneOf(
            ["assigned", "accepted", "in_progress", "completed", "rejected"]
        ),
    )
    notes = fields.Str(validate=validate.Length(max=1000), allow_none=True)


class AssignComplaintBodySchema(Schema):
    """Schema for body of POST /admin/complaints/<id>/assign."""

    worker_id = fields.Int(required=True)
    notes = fields.Str(validate=validate.Length(max=1000), allow_none=True)
