"""Administrator namespace — Marshmallow schemas."""

from app.schemas.complaint_schema import (
    ComplaintSchema,
    ComplaintUpdateSchema,
    AdminComplaintUpdateSchema,
)
from app.schemas.assignment_schema import (
    AssignmentSchema,
    AssignmentCreateSchema,
    AssignComplaintBodySchema,
)
from app.schemas.user_schema import (
    UserSchema,
    UserUpdateSchema,
    MunicipalAdminCreateSchema,
    MunicipalAdminUpdateSchema,
)

__all__ = [
    "ComplaintSchema",
    "ComplaintUpdateSchema",
    "AdminComplaintUpdateSchema",
    "AssignmentSchema",
    "AssignmentCreateSchema",
    "AssignComplaintBodySchema",
    "UserSchema",
    "UserUpdateSchema",
    "MunicipalAdminCreateSchema",
    "MunicipalAdminUpdateSchema",
]
