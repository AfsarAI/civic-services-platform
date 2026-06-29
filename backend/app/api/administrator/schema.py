"""
Administrator namespace — Marshmallow schemas.
"""

from app.schemas.complaint_schema import ComplaintSchema, ComplaintUpdateSchema
from app.schemas.assignment_schema import AssignmentSchema, AssignmentCreateSchema
from app.schemas.user_schema import UserSchema, UserUpdateSchema

__all__ = [
    "ComplaintSchema",
    "ComplaintUpdateSchema",
    "AssignmentSchema",
    "AssignmentCreateSchema",
    "UserSchema",
    "UserUpdateSchema",
]
