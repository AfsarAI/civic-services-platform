"""
Schemas package.
"""

from app.schemas.user_schema import UserSchema, UserCreateSchema, UserUpdateSchema
from app.schemas.complaint_schema import ComplaintSchema, ComplaintCreateSchema, ComplaintUpdateSchema
from app.schemas.assignment_schema import AssignmentSchema, AssignmentCreateSchema
from app.schemas.notification_schema import NotificationSchema
from app.schemas.feedback_schema import FeedbackSchema, FeedbackCreateSchema

__all__ = [
    "UserSchema",
    "UserCreateSchema",
    "UserUpdateSchema",
    "ComplaintSchema",
    "ComplaintCreateSchema",
    "ComplaintUpdateSchema",
    "AssignmentSchema",
    "AssignmentCreateSchema",
    "NotificationSchema",
    "FeedbackSchema",
    "FeedbackCreateSchema",
]
