"""
Field Worker namespace — Marshmallow schemas.
"""

from app.schemas.assignment_schema import (
    AssignmentSchema,
    AssignmentUpdateSchema,
    FieldWorkerProgressSchema,
)

__all__ = ["AssignmentSchema", "AssignmentUpdateSchema", "FieldWorkerProgressSchema"]
