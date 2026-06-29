"""
Citizen namespace — Marshmallow schemas.
"""

from app.schemas.complaint_schema import ComplaintSchema, ComplaintCreateSchema, ComplaintUpdateSchema
from app.schemas.feedback_schema import FeedbackSchema, FeedbackCreateSchema

__all__ = [
    "ComplaintSchema",
    "ComplaintCreateSchema",
    "ComplaintUpdateSchema",
    "FeedbackSchema",
    "FeedbackCreateSchema",
]
