"""
System settings service — get/update the singleton platform configuration.
"""

from app.extensions import db
from app.models.system_setting import SystemSetting
from app.services.audit_log_service import AuditLogService


class SystemSettingsService:
    """Manages the singleton SystemSetting row (TPS-99)."""

    UPDATABLE_FIELDS = (
        "site_name",
        "support_email",
        "maintenance_mode",
        "notify_on_status_change",
        "default_complaint_priority",
    )

    @staticmethod
    def get_settings() -> SystemSetting:
        """Return the current settings, creating a default row if missing."""
        setting = SystemSetting.query.first()
        if not setting:
            setting = SystemSetting()
            db.session.add(setting)
            db.session.commit()
        return setting

    @staticmethod
    def update_settings(data: dict, updated_by_id: int) -> SystemSetting:
        """Update the singleton settings row and record an audit-log entry."""
        setting = SystemSettingsService.get_settings()

        for field in SystemSettingsService.UPDATABLE_FIELDS:
            if field in data:
                setattr(setting, field, data[field])
        setting.updated_by_id = updated_by_id

        db.session.commit()

        AuditLogService.record_action(
            user_id=updated_by_id,
            action="system_settings_updated",
            resource_type="system_setting",
            resource_id=setting.id,
            details={"updated_fields": sorted(k for k in data if k in SystemSettingsService.UPDATABLE_FIELDS)},
        )
        return setting

    @staticmethod
    def is_maintenance_mode() -> bool:
        """Return True if the platform is currently in maintenance mode."""
        return SystemSettingsService.get_settings().maintenance_mode

    @staticmethod
    def notifications_enabled() -> bool:
        """Return True if automatic status-change notifications should be sent."""
        return SystemSettingsService.get_settings().notify_on_status_change

    @staticmethod
    def serialize(setting: SystemSetting) -> dict:
        return {
            "id": setting.id,
            "site_name": setting.site_name,
            "support_email": setting.support_email,
            "maintenance_mode": setting.maintenance_mode,
            "notify_on_status_change": setting.notify_on_status_change,
            "default_complaint_priority": setting.default_complaint_priority,
            "updated_at": setting.updated_at.isoformat() if setting.updated_at else None,
            "updated_by_id": setting.updated_by_id,
        }
