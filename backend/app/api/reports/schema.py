"""
Reports namespace — Marshmallow schemas.
"""

from marshmallow import Schema, fields


class ComplaintSummarySchema(Schema):
    total = fields.Int()
    pending = fields.Int()
    assigned = fields.Int()
    in_progress = fields.Int()
    resolved = fields.Int()
    closed = fields.Int()
    rejected = fields.Int()
