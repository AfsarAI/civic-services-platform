"""
Notification schemas — serialisation for Notification objects.
"""

from marshmallow import Schema, fields


class NotificationSchema(Schema):
    """Schema for serialising Notification objects."""

    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    title = fields.Str(dump_only=True)
    message = fields.Str(dump_only=True)
    notification_type = fields.Str(dump_only=True)
    is_read = fields.Bool(dump_only=True)
    related_complaint_id = fields.Int(dump_only=True, allow_none=True)
    related_assignment_id = fields.Int(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    read_at = fields.DateTime(dump_only=True, allow_none=True)
