"""Administrator namespace — Marshmallow schemas."""

from app.schemas.complaint_schema import (
    ComplaintSchema,
    ComplaintUpdateSchema,
    AdminComplaintUpdateSchema,
    MarkDuplicateSchema,
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
    FieldWorkerCreateSchema,
    FieldWorkerUpdateSchema,
)
from app.schemas.system_setting_schema import SystemSettingUpdateSchema
from app.schemas.verification_schema import VerificationDecisionSchema

__all__ = [
    "ComplaintSchema",
    "ComplaintUpdateSchema",
    "AdminComplaintUpdateSchema",
    "MarkDuplicateSchema",
    "AssignmentSchema",
    "AssignmentCreateSchema",
    "AssignComplaintBodySchema",
    "UserSchema",
    "UserUpdateSchema",
    "MunicipalAdminCreateSchema",
    "MunicipalAdminUpdateSchema",
    "FieldWorkerCreateSchema",
    "FieldWorkerUpdateSchema",
    "SystemSettingUpdateSchema",
    "VerificationDecisionSchema",
]
