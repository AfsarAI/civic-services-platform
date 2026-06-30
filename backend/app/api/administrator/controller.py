"""
Administrator controller — complaint management, user management, assignments.

All endpoints require administrator role.
Covered Jira stories: TPS-78 to TPS-85, TPS-95 to TPS-99
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.administrator.schema import (
    AdminComplaintUpdateSchema,
    AssignComplaintBodySchema,
    UserUpdateSchema,
)
from app.api.administrator.service import AdminService
from app.utils.decorators import validate_body, require_admin
from app.utils.responses import success_response, error_response, paginated_response

ns = Namespace("admin", description="Administrator operations", path="/admin")
_svc = AdminService()

# ── Swagger models (docs only) ────────────────────────────────────────────

_envelope = ns.model("AdminEnvelope", {
    "success": fields.Boolean,
    "message": fields.String,
    "data": fields.Raw,
    "errors": fields.Raw,
})

_complaint_update = ns.model("AdminComplaintUpdate", {
    "status": fields.String(
        example="resolved",
        enum=["pending", "assigned", "in_progress", "resolved", "closed", "rejected"],
    ),
    "priority": fields.String(
        example="high", enum=["low", "medium", "high", "urgent"]
    ),
})

_assign_body = ns.model("AssignComplaint", {
    "worker_id": fields.Integer(required=True, example=3),
    "notes": fields.String(example="Urgent — please inspect by end of day."),
})

_user_update = ns.model("AdminUserUpdate", {
    "first_name": fields.String,
    "last_name": fields.String,
    "phone": fields.String,
    "is_active": fields.Boolean(example=True),
})


# ── Complaint management ──────────────────────────────────────────────────

@ns.route("/complaints")
class AdminComplaintListResource(Resource):

    @ns.response(200, "Paginated complaints", _envelope)
    @ns.response(401, "Unauthorised")
    @ns.response(403, "Forbidden")
    @jwt_required()
    @require_admin
    def get(self):
        """List all complaints (TPS-78).

        Query params: page, per_page, status, category, priority, citizen_id.
        """
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status")
        category = request.args.get("category")
        priority = request.args.get("priority")
        citizen_id = request.args.get("citizen_id", type=int)

        try:
            result = _svc.get_all_complaints(
                page, per_page, status, category, priority, citizen_id
            )
            return paginated_response(
                result["items"], result["total"],
                result["page"], result["per_page"],
                "Complaints retrieved.",
            )
        except ValueError as exc:
            return error_response(str(exc), status_code=400)


@ns.route("/complaints/<int:complaint_id>")
@ns.param("complaint_id", "Complaint ID")
class AdminComplaintResource(Resource):

    @ns.response(200, "Complaint details", _envelope)
    @ns.response(404, "Not found", _envelope)
    @jwt_required()
    @require_admin
    def get(self, complaint_id):
        """Get full complaint details including assignment and feedback (TPS-79)."""
        try:
            data = _svc.get_complaint(complaint_id)
            return success_response(data, "Complaint retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=404)

    @ns.expect(_complaint_update)
    @ns.response(200, "Complaint updated", _envelope)
    @ns.response(422, "Validation error", _envelope)
    @jwt_required()
    @require_admin
    @validate_body(AdminComplaintUpdateSchema)
    def put(self, body, complaint_id):
        """Update a complaint's status and/or priority (TPS-80, TPS-83)."""
        try:
            data = _svc.update_complaint(complaint_id, body)
            return success_response(data, "Complaint updated successfully.")
        except ValueError as exc:
            code = 404 if "not found" in str(exc).lower() else 400
            return error_response(str(exc), status_code=code)


@ns.route("/complaints/<int:complaint_id>/assign")
@ns.param("complaint_id", "Complaint ID")
class AdminAssignComplaintResource(Resource):

    @ns.expect(_assign_body)
    @ns.response(201, "Complaint assigned", _envelope)
    @ns.response(400, "Business rule violation", _envelope)
    @ns.response(422, "Validation error", _envelope)
    @jwt_required()
    @require_admin
    @validate_body(AssignComplaintBodySchema)
    def post(self, body, complaint_id):
        """Assign a complaint to a field worker (TPS-81)."""
        admin_id = int(get_jwt_identity())
        try:
            data = _svc.assign_complaint(complaint_id, admin_id, body)
            return success_response(data, "Complaint assigned successfully.", 201)
        except ValueError as exc:
            code = 404 if "not found" in str(exc).lower() else 400
            return error_response(str(exc), status_code=code)


# ── User management ───────────────────────────────────────────────────────

@ns.route("/users")
class AdminUserListResource(Resource):

    @ns.response(200, "Paginated users", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """List all platform users (TPS-95).

        Query params: page, per_page, role, is_active (true/false).
        """
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        role = request.args.get("role")
        is_active_str = request.args.get("is_active")
        is_active = None
        if is_active_str is not None:
            is_active = is_active_str.lower() == "true"

        try:
            result = _svc.get_all_users(page, per_page, role, is_active)
            return paginated_response(
                result["items"], result["total"],
                result["page"], result["per_page"],
                "Users retrieved.",
            )
        except ValueError as exc:
            return error_response(str(exc), status_code=400)


@ns.route("/users/<int:user_id>")
@ns.param("user_id", "User ID")
class AdminUserResource(Resource):

    @ns.response(200, "User details", _envelope)
    @ns.response(404, "Not found", _envelope)
    @jwt_required()
    @require_admin
    def get(self, user_id):
        """Get a specific user's details (TPS-96)."""
        try:
            data = _svc.get_user(user_id)
            return success_response(data, "User retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=404)

    @ns.expect(_user_update)
    @ns.response(200, "User updated", _envelope)
    @ns.response(422, "Validation error", _envelope)
    @jwt_required()
    @require_admin
    @validate_body(UserUpdateSchema)
    def put(self, body, user_id):
        """Update a user's profile or active status (TPS-97)."""
        admin_id = int(get_jwt_identity())
        try:
            data = _svc.update_user(user_id, admin_id, body)
            return success_response(data, "User updated successfully.")
        except ValueError as exc:
            code = 404 if "not found" in str(exc).lower() else 400
            return error_response(str(exc), status_code=code)


# ── Field workers ─────────────────────────────────────────────────────────

@ns.route("/field-workers")
class AdminFieldWorkerListResource(Resource):

    @ns.response(200, "Active field workers", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """List all active field workers for the assignment dropdown (TPS-82)."""
        data = _svc.get_field_workers()
        return success_response(data, "Field workers retrieved.")


# ── Dashboard ─────────────────────────────────────────────────────────────

@ns.route("/dashboard")
class AdminDashboardResource(Resource):

    @ns.response(200, "Dashboard summary", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Get platform-wide complaint and user statistics (TPS-85)."""
        data = _svc.get_dashboard_summary()
        return success_response(data, "Dashboard data retrieved.")
