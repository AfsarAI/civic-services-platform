"""
Service helpers for audit-log persistence.
"""

from flask import current_app

from app.extensions import db
from app.models.audit_log import AuditLog


class AuditLogService:
    """Write immutable audit-log entries for sensitive actions."""

    @staticmethod
    def record_action(
        *,
        user_id: int | None,
        action: str,
        resource_type: str,
        resource_id: int | None = None,
        details: dict | None = None,
    ) -> None:
        db.session.add(
            AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
            )
        )
        current_app.logger.info(
            "Audit event recorded",
            extra={
                "audit_action": action,
                "audit_user_id": user_id,
                "audit_resource_type": resource_type,
                "audit_resource_id": resource_id,
            },
        )
