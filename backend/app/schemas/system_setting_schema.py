"""
System settings schemas — validation for the singleton SystemSetting row.
"""

from marshmallow import Schema, fields, pre_load, validate

from app.schemas.validators import normalize_email, normalize_optional_string, normalize_string


class SystemSettingUpdateSchema(Schema):
    """Schema for updating platform-wide system settings (system admin only).

    All fields are optional — only the fields provided are changed.
    """

    site_name = fields.Str(validate=validate.Length(min=1, max=120))
    support_email = fields.Email(allow_none=True)
    maintenance_mode = fields.Bool()
    notify_on_status_change = fields.Bool()
    default_complaint_priority = fields.Str(
        validate=validate.OneOf(["low", "medium", "high", "urgent"])
    )
    duplicate_detection_radius_meters = fields.Int(
        validate=validate.Range(min=10, max=2000)
    )

    @pre_load
    def normalize_fields(self, data: dict, **_) -> dict:
        if "site_name" in data:
            data["site_name"] = normalize_string(data.get("site_name"))
        if "support_email" in data and data.get("support_email") is not None:
            data["support_email"] = normalize_optional_string(normalize_email(data.get("support_email")))
        return data
