"""
Administrator service — business logic for admin-facing operations.
"""

from datetime import datetime, timezone
from flask import current_app
from sqlalchemy import and_, func, not_
from sqlalchemy.exc import IntegrityError

from app.api.notifications.service import NotificationService
from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.city import City
from app.models.complaint import Complaint
from app.models.complaint_assignment import ComplaintAssignment
from app.models.complaint_verification import ComplaintVerification
from app.models.notification import Notification
from app.models.role import Role
from app.models.user import User
from app.repositories import AdministratorRepository
from app.services.audit_log_service import AuditLogService
from app.services.system_settings_service import SystemSettingsService


class VerificationConflictError(ValueError):
    """Raised when a repair completion has already been verified."""


class AdminService:
    """Handles complaint management, admin hierarchy, and platform statistics."""

    def __init__(self):
        self.repository = AdministratorRepository()
        self.notifications = NotificationService()

    # ── Complaints ────────────────────────────────────────────────────────

    def get_all_complaints(
        self,
        page: int = 1,
        per_page: int = 20,
        status: str = None,
        category: str = None,
        priority: str = None,
        citizen_id: int = None,
        city_id: int = None,
    ) -> dict:
        """Return paginated complaints, optionally filtered.

        Args:
            city_id: When provided (municipal administrators), restricts the
                result set to complaints filed in that city. ``None`` means
                unscoped (system administrators see every city).
        """
        per_page = min(per_page, 100)
        query = Complaint.query

        if city_id is not None:
            query = query.filter_by(city_id=city_id)
        if status:
            if status not in Complaint.VALID_STATUSES:
                raise ValueError(f"Invalid status '{status}'.")
            query = query.filter_by(status=status)
        if category:
            query = query.filter_by(category=category)
        if priority:
            query = query.filter_by(priority=priority)
        if citizen_id:
            query = query.filter_by(citizen_id=citizen_id)

        query = query.order_by(Complaint.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": [self._serialize_complaint(c) for c in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
        }

    def get_complaint(self, complaint_id: int, city_id: int = None) -> dict:
        """Return full complaint details including assignment and feedback.

        Args:
            city_id: When provided, the complaint must belong to this city
                or a ``ValueError`` (treated as 404) is raised.
        """
        complaint = Complaint.query.get(complaint_id)
        if not complaint or (city_id is not None and complaint.city_id != city_id):
            raise ValueError("Complaint not found.")
        return {"complaint": self._serialize_complaint(complaint, full=True)}

    def get_assignment_monitor(
        self,
        page: int = 1,
        per_page: int = 20,
        status: str = None,
        overdue: bool = None,
        city_id: int = None,
    ) -> dict:
        """Return latest assignment progress for administrator monitoring."""
        valid_statuses = (
            ComplaintAssignment.STATUS_ASSIGNED,
            ComplaintAssignment.STATUS_ACCEPTED,
            ComplaintAssignment.STATUS_IN_PROGRESS,
            ComplaintAssignment.STATUS_COMPLETED,
            ComplaintAssignment.STATUS_REJECTED,
        )
        if status and status not in valid_statuses:
            raise ValueError(f"Invalid assignment status '{status}'.")

        per_page = min(max(per_page, 1), 100)
        query = ComplaintAssignment.query.join(Complaint)
        if city_id is not None:
            query = query.filter(Complaint.city_id == city_id)
        if status:
            query = query.filter(ComplaintAssignment.status == status)

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        overdue_filter = and_(
            ComplaintAssignment.expected_completion_at.isnot(None),
            ComplaintAssignment.expected_completion_at < now,
            ComplaintAssignment.status.notin_(
                (
                    ComplaintAssignment.STATUS_COMPLETED,
                    ComplaintAssignment.STATUS_REJECTED,
                )
            ),
            Complaint.status.notin_(
                (
                    Complaint.STATUS_RESOLVED,
                    Complaint.STATUS_CLOSED,
                    Complaint.STATUS_REJECTED,
                    Complaint.STATUS_CANCELLED,
                )
            ),
        )
        if overdue is True:
            query = query.filter(overdue_filter)
        elif overdue is False:
            query = query.filter(not_(overdue_filter))

        query = query.order_by(ComplaintAssignment.assigned_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "items": [
                self._serialize_monitor_assignment(assignment)
                for assignment in pagination.items
            ],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
        }

    def update_complaint(self, complaint_id: int, data: dict, city_id: int = None) -> dict:
        """Update a complaint's status and/or priority.

        Manual status changes by an administrator follow a restricted
        workflow (TPS-82/83/84):
        - ``in_progress`` \u2192 ``resolved`` (verifying the field worker's repair)
        - ``resolved`` \u2192 ``closed`` (final closure after verification)
        - ``pending``/``assigned``/``in_progress`` \u2192 ``rejected`` (any time before closure)

        The citizen is notified whenever the status actually changes.
        """
        complaint = Complaint.query.get(complaint_id)
        if not complaint or (city_id is not None and complaint.city_id != city_id):
            raise ValueError("Complaint not found.")

        status_changed = False
        if "status" in data and data["status"] != complaint.status:
            new_status = data["status"]
            allowed_from = self._ADMIN_STATUS_TRANSITIONS.get(new_status)
            if allowed_from is not None and complaint.status not in allowed_from:
                raise ValueError(
                    f"Cannot move complaint from '{complaint.status}' to '{new_status}'."
                )
            if new_status == Complaint.STATUS_RESOLVED:
                raise ValueError(
                    "Completed repairs must be approved through repair verification."
                )
            complaint.status = new_status
            if new_status == Complaint.STATUS_RESOLVED and not complaint.resolved_at:
                complaint.resolved_at = datetime.now(timezone.utc)
            if new_status == Complaint.STATUS_CLOSED and not complaint.closed_at:
                complaint.closed_at = datetime.now(timezone.utc)
            status_changed = True

        # Update priority level to adjust complaint triage and urgency.
        if "priority" in data:
            complaint.priority = data["priority"]

        db.session.commit()

        if status_changed:
            self._notify_citizen_status_change(complaint)
            self._notify_worker_status_change(complaint)

        return {"complaint": self._serialize_complaint(complaint, full=True)}

    def verify_repair(
        self,
        complaint_id: int,
        administrator_id: int,
        data: dict,
        city_id: int = None,
    ) -> dict:
        """Approve completed work or request rework from the assigned worker."""
        complaint = Complaint.query.get(complaint_id)
        if not complaint or (city_id is not None and complaint.city_id != city_id):
            raise ValueError("Complaint not found.")

        assignment = complaint.assignments.order_by(
            ComplaintAssignment.assigned_at.desc()
        ).first()
        if (
            complaint.status != Complaint.STATUS_IN_PROGRESS
            or not assignment
            or assignment.status != ComplaintAssignment.STATUS_COMPLETED
            or not assignment.completed_at
        ):
            raise ValueError(
                "Only completed repair work awaiting verification can be reviewed."
            )

        decision = data["decision"]
        remarks = (data.get("remarks") or "").strip()
        if (
            decision == ComplaintVerification.DECISION_REWORK_REQUESTED
            and not remarks
        ):
            raise ValueError(
                "Administrator remarks are required when requesting rework."
            )

        # Resolve the optional setting before staging transaction state because
        # the singleton settings helper may lazily create and commit its row.
        notify_citizen = (
            decision == ComplaintVerification.DECISION_APPROVED
            and SystemSettingsService.notifications_enabled()
        )

        try:
            verification = ComplaintVerification(
                complaint_id=complaint.id,
                assignment_id=assignment.id,
                administrator_id=administrator_id,
                decision=decision,
                remarks=remarks or None,
                repair_completed_at=assignment.completed_at,
            )
            db.session.add(verification)

            if decision == ComplaintVerification.DECISION_APPROVED:
                complaint.status = Complaint.STATUS_RESOLVED
                complaint.resolved_at = datetime.now(timezone.utc)
            else:
                assignment.status = ComplaintAssignment.STATUS_IN_PROGRESS

            AuditLogService.record_action(
                user_id=administrator_id,
                action=f"repair_verification_{decision}",
                resource_type="complaint",
                resource_id=complaint.id,
                details={
                    "assignment_id": assignment.id,
                    "decision": decision,
                    "remarks": remarks or None,
                },
            )

            if notify_citizen:
                self._notify_citizen_status_change(
                    complaint,
                    commit=False,
                    notifications_enabled=True,
                )
            elif decision == ComplaintVerification.DECISION_REWORK_REQUESTED:
                # Rework is an operational task notification and is mandatory,
                # independent of the optional automatic-status setting.
                self.notifications.send_notification(
                    user_id=assignment.worker_id,
                    title="Repair rework requested",
                    message=(
                        f"Rework was requested for complaint '{complaint.title}'. "
                        f"Administrator remarks: {remarks}"
                    ),
                    notification_type=Notification.TYPE_STATUS_UPDATE,
                    related_complaint_id=complaint.id,
                    commit=False,
                )

            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            if self._is_verification_conflict(exc):
                raise VerificationConflictError(
                    "This repair completion has already been verified."
                ) from exc
            raise
        except Exception:
            db.session.rollback()
            raise

        return {
            "verification": self._serialize_verification(verification),
            "complaint": self._serialize_complaint(complaint, full=True),
        }

    @staticmethod
    def _is_verification_conflict(exc: IntegrityError) -> bool:
        constraint_name = getattr(
            getattr(exc.orig, "diag", None),
            "constraint_name",
            None,
        )
        if constraint_name == "uq_verification_assignment_completion":
            return True
        message = str(exc.orig).lower()
        return (
            "complaint_verifications.assignment_id" in message
            and "complaint_verifications.repair_completed_at" in message
        )

    # Statuses an administrator may manually move a complaint *to*, and the
    # statuses it is allowed to come *from*. Any status not listed here
    # (e.g. re-setting the same status) has no restriction.
    _ADMIN_STATUS_TRANSITIONS = {
        Complaint.STATUS_RESOLVED: (Complaint.STATUS_IN_PROGRESS,),
        Complaint.STATUS_CLOSED: (Complaint.STATUS_RESOLVED,),
        Complaint.STATUS_REJECTED: (
            Complaint.STATUS_PENDING,
            Complaint.STATUS_ASSIGNED,
            Complaint.STATUS_IN_PROGRESS,
        ),
    }

    def _notify_citizen_status_change(
        self,
        complaint: Complaint,
        *,
        commit: bool = True,
        notifications_enabled: bool = None,
    ) -> None:
        """Notify the citizen who filed the complaint about a status change.

        Skipped entirely when the system administrator has turned automatic
        status-change notifications off via system settings.
        """
        enabled = (
            SystemSettingsService.notifications_enabled()
            if notifications_enabled is None
            else notifications_enabled
        )
        if not enabled:
            return

        closed_at_display = (
            complaint.closed_at.strftime("%B %d, %Y") if complaint.closed_at else "recently"
        )
        status_messages = {
            Complaint.STATUS_RESOLVED: (
                "Complaint resolved",
                f"Your complaint #{complaint.id} '{complaint.title}' has been marked as resolved. "
                "Please share your feedback.",
                Notification.TYPE_COMPLAINT_RESOLVED,
            ),
            Complaint.STATUS_CLOSED: (
                "Complaint closed",
                f"Your complaint #{complaint.id} '{complaint.title}' was officially closed on "
                f"{closed_at_display}. Please share your feedback on the repair.",
                Notification.TYPE_STATUS_UPDATE,
            ),
            Complaint.STATUS_REJECTED: (
                "Complaint rejected",
                f"Your complaint #{complaint.id} '{complaint.title}' was rejected by the administrator.",
                Notification.TYPE_STATUS_UPDATE,
            ),
        }
        entry = status_messages.get(complaint.status)
        if not entry:
            return
        title, message, notif_type = entry
        self.notifications.send_notification(
            user_id=complaint.citizen_id,
            title=title,
            message=message,
            notification_type=notif_type,
            related_complaint_id=complaint.id,
            commit=commit,
        )

    def _notify_worker_status_change(self, complaint: Complaint) -> None:
        """Notify the field worker last assigned to this complaint when an
        administrator rejects or closes it, so an actively-working worker
        knows to stop, and a completed worker gets closure confirmation.

        Skipped for ``resolved`` (the worker already knows — they're the ones
        who triggered the completion that led to it) and gated on the same
        system setting as citizen notifications.
        """
        if not SystemSettingsService.notifications_enabled():
            return

        latest_assignment = complaint.assignments.order_by(
            ComplaintAssignment.assigned_at.desc()
        ).first()
        if not latest_assignment:
            return

        status_messages = {
            Complaint.STATUS_REJECTED: (
                "Complaint rejected — stop work",
                f"The complaint #{complaint.id} '{complaint.title}' was rejected by an administrator. "
                "No further action is needed on this task.",
            ),
            Complaint.STATUS_CLOSED: (
                "Complaint closed",
                f"The complaint #{complaint.id} '{complaint.title}' has been verified and closed. "
                "Thank you for completing this repair.",
            ),
        }
        entry = status_messages.get(complaint.status)
        if not entry:
            return
        title, message = entry
        self.notifications.send_notification(
            user_id=latest_assignment.worker_id,
            title=title,
            message=message,
            notification_type=Notification.TYPE_STATUS_UPDATE,
            related_complaint_id=complaint.id,
        )

    def assign_complaint(
        self, complaint_id: int, admin_id: int, data: dict, city_id: int = None
    ) -> dict:
        """Assign a complaint to a field worker.

        Args:
            city_id: When provided (municipal administrators), the complaint
                and the field worker must both belong to this city.
        """
        complaint = Complaint.query.get(complaint_id)
        if not complaint or (city_id is not None and complaint.city_id != city_id):
            raise ValueError("Complaint not found.")

        if complaint.status not in (
            Complaint.STATUS_PENDING, Complaint.STATUS_ASSIGNED
        ):
            raise ValueError(
                "Only pending or already-assigned complaints can be assigned. "
                f"Current status: '{complaint.status}'."
            )

        # Verify field worker eligibility and city scoping before creating complaint assignment.
        worker = User.query.get(data["worker_id"])
        if not worker:
            raise ValueError("Field worker not found.")

        worker_role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
        if not worker_role or worker.role_id != worker_role.id:
            raise ValueError("The specified user is not a field worker.")

        if not worker.is_active:
            raise ValueError("The specified field worker is inactive.")

        if city_id is not None and worker.city_id != city_id:
            raise ValueError("The specified field worker does not belong to your city.")

        assignment = ComplaintAssignment(
            complaint_id=complaint_id,
            worker_id=data["worker_id"],
            assigned_by_id=admin_id,
            status=ComplaintAssignment.STATUS_ASSIGNED,
            expected_completion_at=data.get("expected_completion_at"),
            notes=data.get("notes"),
        )
        db.session.add(assignment)
        complaint.status = Complaint.STATUS_ASSIGNED
        db.session.commit()

        if SystemSettingsService.notifications_enabled():
            self.notifications.send_notification(
                user_id=worker.id,
                title="New task assigned",
                message=f"You have been assigned a new complaint #{complaint.id}: '{complaint.title}'.",
                notification_type=Notification.TYPE_COMPLAINT_ASSIGNED,
                related_complaint_id=complaint.id,
            )
            self.notifications.send_notification(
                user_id=complaint.citizen_id,
                title="Complaint assigned",
                message=f"Your complaint #{complaint.id} '{complaint.title}' has been assigned to a field worker.",
                notification_type=Notification.TYPE_STATUS_UPDATE,
                related_complaint_id=complaint.id,
            )

        return {
            "assignment": self._serialize_assignment(assignment),
            "complaint": self._serialize_complaint(complaint),
        }

    # ── Users ─────────────────────────────────────────────────────────────

    def get_all_users(
        self,
        page: int = 1,
        per_page: int = 20,
        role: str = None,
        is_active: bool = None,
    ) -> dict:
        """Return paginated users, optionally filtered by role or active flag."""
        per_page = min(per_page, 100)
        query = User.query

        if role:
            role_obj = Role.query.filter_by(name=role).first()
            if not role_obj:
                raise ValueError(f"Unknown role '{role}'.")
            query = query.filter_by(role_id=role_obj.id)

        if is_active is not None:
            query = query.filter_by(is_active=is_active)

        query = query.order_by(User.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": [self._serialize_user(u) for u in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
        }

    def get_user(self, user_id: int) -> dict:
        """Return user details."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found.")
        return {"user": self._serialize_user(user)}

    def update_user(self, user_id: int, admin_id: int, data: dict) -> dict:
        """Update a user's profile fields or active status."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found.")

        if "is_active" in data and not data["is_active"] and user_id == admin_id:
            raise ValueError("You cannot deactivate your own account.")

        for field in ("first_name", "last_name", "phone", "is_active"):
            if field in data:
                setattr(user, field, data[field])

        db.session.commit()
        return {"user": self._serialize_user(user)}

    def get_field_workers(self, acting_admin: User = None, is_active: bool = None) -> dict:
        """Return field workers, optionally filtered by active status.

        Municipal administrators only see field workers that belong to their
        own city; system administrators see field workers across all cities.
        """
        fw_role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
        if not fw_role:
            return {"field_workers": []}

        query = User.query.filter_by(role_id=fw_role.id)
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        if acting_admin is not None and acting_admin.is_municipal_admin:
            query = query.filter_by(city_id=acting_admin.admin_city_id)

        workers = query.order_by(User.first_name).all()
        return {"field_workers": [self._serialize_user(w) for w in workers]}

    def create_field_worker(self, acting_admin: User, data: dict) -> dict:
        """Create a field worker in the acting municipal administrator's city.

        Field workers are always created by a municipal administrator and are
        automatically scoped to that administrator's own city — the city is
        never accepted from the request body.
        """
        city_id = acting_admin.admin_city_id
        if not city_id:
            raise ValueError("Your administrator account is not scoped to a city.")

        email = data["email"].strip().lower()
        if self.repository.get_user_by_email(email):
            raise ValueError("An account with this email already exists.")

        username = data["username"].strip()
        if self.repository.get_user_by_username(username):
            raise ValueError("This username is already taken.")

        fw_role = self.repository.get_role_by_name(Role.FIELD_WORKER)
        if not fw_role:
            raise RuntimeError("Field worker role not found. Run 'flask seed' first.")

        worker = self.repository.create_user(
            username=username,
            email=email,
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone=data.get("phone"),
            role_id=fw_role.id,
            city_id=city_id,
            is_active=True,
        )
        worker.set_password(data["password"])
        db.session.flush()

        AuditLogService.record_action(
            user_id=acting_admin.id,
            action="field_worker_created",
            resource_type="user",
            resource_id=worker.id,
            details={"email": worker.email, "city_id": city_id},
        )
        db.session.commit()
        current_app.logger.info(
            "Field worker created",
            extra={"creator_id": acting_admin.id, "field_worker_id": worker.id, "city_id": city_id},
        )
        return {"user": self._serialize_user(worker)}

    def get_field_worker(self, user_id: int, acting_admin: User) -> dict:
        """Return details for one field worker, enforcing city ownership."""
        worker = self._get_owned_field_worker(user_id, acting_admin)
        return {"user": self._serialize_user(worker)}

    def update_field_worker(self, user_id: int, acting_admin: User, data: dict) -> dict:
        """Edit or activate/deactivate a field worker owned by the acting administrator's city."""
        worker = self._get_owned_field_worker(user_id, acting_admin)

        for field in ("first_name", "last_name", "phone", "is_active"):
            if field in data:
                setattr(worker, field, data[field])

        AuditLogService.record_action(
            user_id=acting_admin.id,
            action="field_worker_updated",
            resource_type="user",
            resource_id=worker.id,
            details={"updated_fields": sorted(list(data.keys())), "is_active": worker.is_active},
        )
        db.session.commit()
        current_app.logger.info(
            "Field worker updated",
            extra={"acting_admin_id": acting_admin.id, "field_worker_id": worker.id},
        )
        return {"user": self._serialize_user(worker)}

    @staticmethod
    def _get_owned_field_worker(user_id: int, acting_admin: User) -> User:
        """Fetch a field worker, enforcing city ownership for municipal administrators.

        Raises:
            ValueError: If not found, not a field worker, or (for municipal
                administrators) belonging to a different city.
        """
        fw_role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
        worker = User.query.get(user_id)
        if not worker or not fw_role or worker.role_id != fw_role.id:
            raise ValueError("Field worker not found.")
        if acting_admin.is_municipal_admin and worker.city_id != acting_admin.admin_city_id:
            raise ValueError("Field worker not found.")
        return worker

    # ── Admin hierarchy ───────────────────────────────────────────────────

    def get_cities(self) -> dict:
        """Return all cities available for municipal administrator assignment."""
        cities = self.repository.list_cities()
        return {"cities": [self._serialize_city(city) for city in cities]}

    def get_municipal_administrators(
        self,
        page: int = 1,
        per_page: int = 20,
        is_active: bool = None,
        city_name: str = None,
    ) -> dict:
        """Return paginated municipal administrators."""
        per_page = min(per_page, 100)
        pagination = self.repository.list_municipal_administrators(
            page=page,
            per_page=per_page,
            is_active=is_active,
            city_name=city_name,
        )

        return {
            "items": [self._serialize_user(user) for user in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
        }

    def create_municipal_administrator(self, creator_id: int, data: dict) -> dict:
        """Create a municipal administrator under the administrator role."""
        email = data["email"].strip().lower()
        if self.repository.get_user_by_email(email):
            raise ValueError("An account with this email already exists.")

        username = data["username"].strip()
        if self.repository.get_user_by_username(username):
            raise ValueError("This username is already taken.")

        admin_role = self.repository.get_role_by_name(Role.ADMINISTRATOR)
        if not admin_role:
            raise RuntimeError("Administrator role not found. Run 'flask seed' first.")

        city = self._resolve_city_for_onboarding(data)

        user = self.repository.create_user(
            username=username,
            email=email,
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone=data.get("phone"),
            pincode=data.get("pincode"),
            role_id=admin_role.id,
            is_active=True,
        )
        user.set_password(data["password"])
        db.session.flush()

        self.repository.create_admin_profile(
            user_id=user.id,
            admin_level=AdministratorProfile.MUNICIPAL,
            city_id=city.id,
            created_by_id=creator_id,
        )

        AuditLogService.record_action(
            user_id=creator_id,
            action="municipal_admin_created",
            resource_type="user",
            resource_id=user.id,
            details={
                "email": user.email,
                "city_id": city.id,
                "city_name": city.name,
                "admin_level": AdministratorProfile.MUNICIPAL,
            },
        )
        db.session.commit()
        current_app.logger.info(
            "Municipal administrator created",
            extra={
                "creator_id": creator_id,
                "municipal_admin_user_id": user.id,
                "city_id": city.id,
            },
        )

        return {"user": self._serialize_user(user)}

    def get_municipal_administrator(self, user_id: int) -> dict:
        """Return details for one municipal administrator."""
        user = self._get_municipal_admin_user(user_id)
        return {"user": self._serialize_user(user)}

    def update_municipal_administrator(
        self,
        user_id: int,
        acting_admin_id: int,
        data: dict,
    ) -> dict:
        """Update or disable a municipal administrator."""
        user = self._get_municipal_admin_user(user_id)

        if "is_active" in data and not data["is_active"] and user_id == acting_admin_id:
            raise ValueError("You cannot deactivate your own account.")

        for field in ("first_name", "last_name", "phone", "is_active"):
            if field in data:
                setattr(user, field, data[field])

        if "pincode" in data or "city_id" in data:
            city = self._resolve_city_from_pincode(data.get("pincode"), data.get("city_id"))
            user.admin_profile.city_id = city.id
            if "pincode" in data:
                user.pincode = data.get("pincode")
        elif "city_name" in data:
            city = self._get_or_create_city(data["city_name"], data.get("city_state"))
            user.admin_profile.city_id = city.id
        elif "city_state" in data and user.admin_profile.city:
            user.admin_profile.city.state = data["city_state"]

        AuditLogService.record_action(
            user_id=acting_admin_id,
            action="municipal_admin_updated",
            resource_type="user",
            resource_id=user.id,
            details={
                "updated_fields": sorted(list(data.keys())),
                "city_id": user.admin_profile.city_id,
                "city_name": user.admin_city_name,
                "is_active": user.is_active,
            },
        )
        db.session.commit()
        current_app.logger.info(
            "Municipal administrator updated",
            extra={
                "acting_admin_id": acting_admin_id,
                "municipal_admin_user_id": user.id,
            },
        )
        return {"user": self._serialize_user(user)}

    # ── System settings (TPS-99) ──────────────────────────────────────────

    def get_system_settings(self) -> dict:
        """Return the current platform-wide system settings."""
        setting = SystemSettingsService.get_settings()
        return {"settings": SystemSettingsService.serialize(setting)}

    def update_system_settings(self, data: dict, admin_id: int) -> dict:
        """Update platform-wide system settings and record an audit-log entry."""
        setting = SystemSettingsService.update_settings(data, admin_id)
        return {"settings": SystemSettingsService.serialize(setting)}

    # ── Dashboard ─────────────────────────────────────────────────────────

    def get_dashboard_summary(self, admin_user: User) -> dict:
        """Return dashboard data depending on administrator subtype."""
        if admin_user.is_system_admin:
            counts = {s: 0 for s in Complaint.VALID_STATUSES}
            for status in Complaint.VALID_STATUSES:
                counts[status] = Complaint.query.filter_by(status=status).count()

            total = Complaint.query.count()
            open_count = Complaint.query.filter(
                Complaint.status.in_([
                    Complaint.STATUS_PENDING,
                    Complaint.STATUS_ASSIGNED,
                    Complaint.STATUS_IN_PROGRESS,
                ])
            ).count()

            recent = (
                Complaint.query
                .order_by(Complaint.created_at.desc())
                .limit(10)
                .all()
            )

            total_users = User.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            municipal_admins = (
                AdministratorProfile.query
                .filter_by(admin_level=AdministratorProfile.MUNICIPAL)
                .count()
            )

            high_priority_open = Complaint.query.filter(
                Complaint.priority == "high",
                Complaint.status.in_([
                    Complaint.STATUS_PENDING,
                    Complaint.STATUS_ASSIGNED,
                    Complaint.STATUS_IN_PROGRESS,
                ]),
            ).count()

            avg_resolution_hours = None
            resolved_with_times = Complaint.query.filter(Complaint.resolved_at.isnot(None))
            if resolved_with_times.count():
                result = resolved_with_times.with_entities(
                    func.avg(
                        (func.julianday(Complaint.resolved_at) -
                         func.julianday(Complaint.created_at)) * 24
                    )
                ).scalar()
                if result is not None:
                    avg_resolution_hours = round(float(result), 1)

            fw_role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
            fw_query = (
                User.query.filter_by(role_id=fw_role.id) if fw_role else User.query.filter(False)
            )
            active_field_workers = fw_query.filter_by(is_active=True).count()

            return {
                "scope": "system",
                "total_complaints": total,
                "open_complaints": open_count,
                "by_status": counts,
                "high_priority_complaints": high_priority_open,
                "avg_resolution_hours": avg_resolution_hours,
                "total_users": total_users,
                "active_users": active_users,
                "total_cities": City.query.count(),
                "municipal_admins": municipal_admins,
                "active_field_workers": active_field_workers,
                "recent_complaints": [self._serialize_complaint(c) for c in recent],
            }

        city_id = admin_user.admin_city_id
        base_query = Complaint.query.filter_by(city_id=city_id)

        counts = {s: base_query.filter_by(status=s).count() for s in Complaint.VALID_STATUSES}
        total = base_query.count()
        open_count = base_query.filter(
            Complaint.status.in_([
                Complaint.STATUS_PENDING,
                Complaint.STATUS_ASSIGNED,
                Complaint.STATUS_IN_PROGRESS,
            ])
        ).count()
        recent = base_query.order_by(Complaint.created_at.desc()).limit(10).all()

        fw_role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
        fw_query = (
            User.query.filter_by(role_id=fw_role.id, city_id=city_id)
            if fw_role else User.query.filter(False)
        )
        total_workers = fw_query.count()
        active_workers = fw_query.filter_by(is_active=True).count()

        high_priority_open = base_query.filter(
            Complaint.priority == "high",
            Complaint.status.in_([
                Complaint.STATUS_PENDING,
                Complaint.STATUS_ASSIGNED,
                Complaint.STATUS_IN_PROGRESS,
            ]),
        ).count()

        avg_resolution_hours = None
        resolved_with_times = base_query.filter(Complaint.resolved_at.isnot(None))
        if resolved_with_times.count():
            result = resolved_with_times.with_entities(
                func.avg(
                    (func.julianday(Complaint.resolved_at) -
                     func.julianday(Complaint.created_at)) * 24
                )
            ).scalar()
            if result is not None:
                avg_resolution_hours = round(float(result), 1)

        return {
            "scope": "municipal",
            "administrator": self._serialize_user(admin_user),
            "managed_city": self._serialize_city(admin_user.admin_profile.city),
            "total_complaints": total,
            "open_complaints": open_count,
            "by_status": counts,
            "high_priority_complaints": high_priority_open,
            "avg_resolution_hours": avg_resolution_hours,
            "total_field_workers": total_workers,
            "active_field_workers": active_workers,
            "recent_complaints": [self._serialize_complaint(c) for c in recent],
        }

    # ── Internal helpers ──────────────────────────────────────────────────

    def _get_or_create_city(self, city_name: str, city_state: str = None) -> City:
        normalized_name = city_name.strip()
        normalized_state = city_state.strip() if isinstance(city_state, str) else city_state
        city = self.repository.find_city_by_name(normalized_name, normalized_state)
        if city:
            if normalized_state and not city.state:
                city.state = normalized_state
                db.session.flush()
            return city

        return self.repository.create_city(normalized_name, normalized_state)

    def _resolve_city_for_onboarding(self, data: dict) -> City:
        pincode = data.get("pincode")
        city_id = data.get("city_id")
        if pincode:
            return self._resolve_city_from_pincode(pincode, city_id)
        if data.get("city_name"):
            return self._get_or_create_city(data["city_name"], data.get("city_state"))
        raise ValueError("Either pincode or city_name is required.")

    def _resolve_city_from_pincode(self, pincode: str | None, city_id: int | None) -> City:
        if not pincode:
            raise ValueError("Pincode is required when selecting city by pincode.")

        mappings = self.repository.find_cities_by_pincode(pincode)
        if not mappings:
            raise ValueError("No city mapping found for the provided pincode.")

        if city_id is not None:
            mapping = self.repository.get_city_pincode_mapping(pincode, city_id)
            if not mapping:
                raise ValueError("Selected city does not match the provided pincode.")
            return mapping.city

        unique_cities = {mapping.city_id: mapping.city for mapping in mappings}
        if len(unique_cities) > 1:
            raise ValueError("Multiple cities found for this pincode. Please select a city.")
        return list(unique_cities.values())[0]

    def _get_municipal_admin_user(self, user_id: int) -> User:
        user = self.repository.get_municipal_admin_user(user_id)
        if not user:
            raise ValueError("Municipal administrator not found.")
        return user

    # ── Serializers ───────────────────────────────────────────────────────

    @staticmethod
    def _serialize_city(city: City | None) -> dict | None:
        if not city:
            return None
        return {
            "id": city.id,
            "name": city.name,
            "state": city.state,
            "is_active": city.is_active,
            "created_at": city.created_at.isoformat() if city.created_at else None,
        }

    @staticmethod
    def _serialize_complaint(complaint: Complaint, full: bool = False) -> dict:
        latest_assignment = complaint.assignments.order_by(
            ComplaintAssignment.assigned_at.desc()
        ).first()
        latest_verification = complaint.verifications.order_by(
            ComplaintVerification.created_at.desc()
        ).first()
        data = {
            "id": complaint.id,
            "title": complaint.title,
            "description": complaint.description,
            "category": complaint.category,
            "status": complaint.status,
            "priority": complaint.priority,
            "latitude": complaint.latitude,
            "longitude": complaint.longitude,
            "address": complaint.address,
            "image_url": complaint.image_url,
            "city_id": complaint.city_id,
            "city_name": complaint.city.name if complaint.city else None,
            "pincode": complaint.pincode,
            "citizen_id": complaint.citizen_id,
            "resolved_at": (
                complaint.resolved_at.isoformat() if complaint.resolved_at else None
            ),
            "closed_at": (
                complaint.closed_at.isoformat() if complaint.closed_at else None
            ),
            "created_at": complaint.created_at.isoformat(),
            "updated_at": complaint.updated_at.isoformat(),
            # Lets the dashboard/list flag "field worker finished, awaiting your
            # verification" even though `status` itself stays `in_progress`.
            "assignment_status": latest_assignment.status if latest_assignment else None,
            "repair_completed_at": (
                latest_assignment.completed_at.isoformat()
                if latest_assignment and latest_assignment.completed_at else None
            ),
            "verification_status": (
                latest_verification.decision
                if latest_verification
                else (
                    "pending"
                    if latest_assignment
                    and latest_assignment.status
                    == ComplaintAssignment.STATUS_COMPLETED
                    else "not_started"
                )
            ),
        }
        if full:
            data["citizen"] = (
                AdminService._serialize_user(complaint.citizen)
                if complaint.citizen else None
            )
            data["assignments"] = [
                AdminService._serialize_assignment(a)
                for a in complaint.assignments.order_by(
                    ComplaintAssignment.assigned_at.desc()
                )
            ]
            data["feedback"] = (
                AdminService._serialize_feedback(complaint.feedback)
                if complaint.feedback else None
            )
            data["verification_history"] = [
                AdminService._serialize_verification(verification)
                for verification in complaint.verifications.order_by(
                    ComplaintVerification.created_at.desc()
                )
            ]
        return data

    @staticmethod
    def _serialize_user(user: User) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "phone": user.phone,
            "is_active": user.is_active,
            "role_id": user.role_id,
            "role": user.role.name if user.role else None,
            "admin_level": user.admin_level,
            "city_id": user.admin_city_id if user.is_administrator else user.city_id,
            "city_name": (
                user.admin_city_name if user.is_administrator
                else (user.city.name if user.city else None)
            ),
            "pincode": user.pincode,
            "created_at": user.created_at.isoformat(),
        }

    @staticmethod
    def _serialize_assignment(assignment: ComplaintAssignment) -> dict:
        return {
            "id": assignment.id,
            "complaint_id": assignment.complaint_id,
            "worker_id": assignment.worker_id,
            "worker_name": assignment.worker.full_name if assignment.worker else None,
            "assigned_by_id": assignment.assigned_by_id,
            "status": assignment.status,
            "notes": assignment.notes,
            "evidence_url": assignment.evidence_url,
            "assigned_at": assignment.assigned_at.isoformat(),
            "expected_completion_at": (
                assignment.expected_completion_at.isoformat()
                if assignment.expected_completion_at
                else None
            ),
            "updated_at": (
                assignment.updated_at.isoformat() if assignment.updated_at else None
            ),
            "accepted_at": (
                assignment.accepted_at.isoformat() if assignment.accepted_at else None
            ),
            "completed_at": (
                assignment.completed_at.isoformat() if assignment.completed_at else None
            ),
        }

    @staticmethod
    def _serialize_monitor_assignment(assignment: ComplaintAssignment) -> dict:
        data = AdminService._serialize_assignment(assignment)
        complaint = assignment.complaint
        expected = assignment.expected_completion_at
        if expected and expected.tzinfo is None:
            expected = expected.replace(tzinfo=timezone.utc)
        is_finished = (
            assignment.status in (
                ComplaintAssignment.STATUS_COMPLETED,
                ComplaintAssignment.STATUS_REJECTED,
            )
            or complaint.status in (
                Complaint.STATUS_RESOLVED,
                Complaint.STATUS_CLOSED,
                Complaint.STATUS_REJECTED,
                Complaint.STATUS_CANCELLED,
            )
        )
        data.update({
            "is_overdue": bool(
                expected
                and expected < datetime.now(timezone.utc)
                and not is_finished
            ),
            "complaint": {
                "id": complaint.id,
                "title": complaint.title,
                "status": complaint.status,
                "priority": complaint.priority,
                "city_name": complaint.city.name if complaint.city else None,
            },
        })
        return data

    @staticmethod
    def _serialize_feedback(feedback) -> dict:
        return {
            "id": feedback.id,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "created_at": feedback.created_at.isoformat(),
        }

    @staticmethod
    def _serialize_verification(
        verification: ComplaintVerification,
    ) -> dict:
        return {
            "id": verification.id,
            "complaint_id": verification.complaint_id,
            "assignment_id": verification.assignment_id,
            "administrator_id": verification.administrator_id,
            "administrator_name": (
                verification.administrator.full_name
                if verification.administrator else None
            ),
            "decision": verification.decision,
            "remarks": verification.remarks,
            "repair_completed_at": (
                verification.repair_completed_at.isoformat()
            ),
            "created_at": verification.created_at.isoformat(),
        }
