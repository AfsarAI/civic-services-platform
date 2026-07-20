"""
Models package — imports all models so SQLAlchemy can discover them.
"""

from app.models.role import Role
from app.models.user import User
from app.models.city import City
from app.models.city_pincode import CityPincode
from app.models.administrator_profile import AdministratorProfile
from app.models.complaint import Complaint
from app.models.complaint_assignment import ComplaintAssignment
from app.models.notification import Notification
from app.models.feedback import Feedback
from app.models.audit_log import AuditLog
from app.models.system_setting import SystemSetting

__all__ = [
    "Role",
    "User",
    "City",
    "CityPincode",
    "AdministratorProfile",
    "Complaint",
    "ComplaintAssignment",
    "Notification",
    "Feedback",
    "AuditLog",
    "SystemSetting",
]
