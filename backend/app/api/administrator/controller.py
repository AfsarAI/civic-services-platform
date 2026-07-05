"""
Administrator controller — complaint management and admin hierarchy operations.

All endpoints require the coarse administrator role. System-administrator-only
actions use an additional subtype check.
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.administrator.schema import (
    AdminComplaintUpdateSchema,
    AssignComplaintBodySchema,
    MunicipalAdminCreateSchema,
    MunicipalAdminUpdateSchema,
    UserUpdateSchema,
)
from app.api.administrator.service import AdminService
from app.models.user import User
from app.utils.decorators import validate_body, require_admin, require_system_admin
from app.utils.responses import success_response, error_response, paginated_response

ns = Namespace("admin", description="Administrator operations", path="/admin")
_svc = AdminService()

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
    "notes": fields.String(example="Urgent - please inspect by end of day."),
})

_user_update = ns.model("AdminUserUpdate", {
    "first_name": fields.String,
    "last_name": fields.String,
    "phone": fields.String,
    "is_active": fields.Boolean(example=True),
})

_municipal_admin_create = ns.model("MunicipalAdminCreate", {
    "username": fields.String(required=True, example="lucknow_admin"),
    "email": fields.String(required=True, example="lucknow.admin@example.com"),
    "password": fields.String(required=True, example="Municipal@123"),
    "confirm_password": fields.String(required=True, example="Municipal@123"),
    "first_name": fields.String(required=True, example="Lucknow"),
    "last_name": fields.String(required=True, example="Administrator"),
    "phone": fields.String(example="+91-9876543210"),
    "city_name": fields.String(required=True, example="Lucknow"),
    "city_state": fields.String(example="Uttar Pradesh"),
})

_municipal_admin_update = ns.model("MunicipalAdminUpdate", {
    "first_name": fields.String,
    "last_name": fields.String,
    "phone": fields.String,
    "is_active": fields.Boolean,
    "city_name": fields.String(example="Varanasi"),
    "city_state": fields.String(example="Uttar Pradesh"),
})


def _current_admin_user() -> User:
    return User.query.get(int(get_jwt_identity()))


@ns.route("/complaints")
class AdminComplaintListResource(Resource):

    @ns.response(200, "Paginated complaints", _envelope)
    @ns.response(401, "Unauthorised")
    @ns.response(403, "Forbidden")
    @jwt_required()
    @require_admin
    def get(self):
        """List all complaints."""
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
        """Get full complaint details including assignment and feedback."""
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
        """Update a complaint's status and/or priority."""
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
        """Assign a complaint to a field worker."""
        admin_id = int(get_jwt_identity())
        try:
            data = _svc.assign_complaint(complaint_id, admin_id, body)
            return success_response(data, "Complaint assigned successfully.", 201)
        except ValueError as exc:
            code = 404 if "not found" in str(exc).lower() else 400
            return error_response(str(exc), status_code=code)


@ns.route("/users")
class AdminUserListResource(Resource):

    @ns.response(200, "Paginated users", _envelope)
    @jwt_required()
    @require_system_admin
    def get(self):
        """List all platform users. Restricted to system administrators."""
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
    @require_system_admin
    def get(self, user_id):
        """Get a specific user's details. Restricted to system administrators."""
        try:
            data = _svc.get_user(user_id)
            return success_response(data, "User retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=404)

    @ns.expect(_user_update)
    @ns.response(200, "User updated", _envelope)
    @ns.response(422, "Validation error", _envelope)
    @jwt_required()
    @require_system_admin
    @validate_body(UserUpdateSchema)
    def put(self, body, user_id):
        """Update a user's profile or active status. Restricted to system administrators."""
        admin_id = int(get_jwt_identity())
        try:
            data = _svc.update_user(user_id, admin_id, body)
            return success_response(data, "User updated successfully.")
        except ValueError as exc:
            code = 404 if "not found" in str(exc).lower() else 400
            return error_response(str(exc), status_code=code)


@ns.route("/municipal-administrators")
class MunicipalAdministratorListResource(Resource):

    @ns.response(200, "Paginated municipal administrators", _envelope)
    @jwt_required()
    @require_system_admin
    def get(self):
        """List municipal administrators."""
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        city_name = request.args.get("city_name")
        is_active_str = request.args.get("is_active")
        is_active = None
        if is_active_str is not None:
            is_active = is_active_str.lower() == "true"

        result = _svc.get_municipal_administrators(
            page=page,
            per_page=per_page,
            is_active=is_active,
            city_name=city_name,
        )
        return paginated_response(
            result["items"],
            result["total"],
            result["page"],
            result["per_page"],
            "Municipal administrators retrieved.",
        )

    @ns.expect(_municipal_admin_create)
    @ns.response(201, "Municipal administrator created", _envelope)
    @ns.response(400, "Business rule violation", _envelope)
    @ns.response(409, "Conflict", _envelope)
    @ns.response(422, "Validation error", _envelope)
    @jwt_required()
    @require_system_admin
    @validate_body(MunicipalAdminCreateSchema)
    def post(self, body):
        """Create a municipal administrator."""
        creator_id = int(get_jwt_identity())
        try:
            data = _svc.create_municipal_administrator(creator_id, body)
            return success_response(data, "Municipal administrator created.", 201)
        except ValueError as exc:
            code = 409 if any(
                token in str(exc).lower() for token in ("already exists", "already taken")
            ) else 400
            return error_response(str(exc), status_code=code)


@ns.route("/municipal-administrators/<int:user_id>")
@ns.param("user_id", "Municipal administrator user ID")
class MunicipalAdministratorResource(Resource):

    @ns.response(200, "Municipal administrator details", _envelope)
    @ns.response(404, "Not found", _envelope)
    @jwt_required()
    @require_system_admin
    def get(self, user_id):
        """Get one municipal administrator."""
        try:
            data = _svc.get_municipal_administrator(user_id)
            return success_response(data, "Municipal administrator retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=404)

    @ns.expect(_municipal_admin_update)
    @ns.response(200, "Municipal administrator updated", _envelope)
    @ns.response(404, "Not found", _envelope)
    @ns.response(400, "Business rule violation", _envelope)
    @ns.response(422, "Validation error", _envelope)
    @jwt_required()
    @require_system_admin
    @validate_body(MunicipalAdminUpdateSchema)
    def put(self, body, user_id):
        """Update or disable a municipal administrator."""
        try:
            data = _svc.update_municipal_administrator(
                user_id=user_id,
                acting_admin_id=int(get_jwt_identity()),
                data=body,
            )
            return success_response(data, "Municipal administrator updated.")
        except ValueError as exc:
            code = 404 if "not found" in str(exc).lower() else 400
            return error_response(str(exc), status_code=code)

    @ns.response(200, "Municipal administrator deactivated", _envelope)
    @ns.response(404, "Not found", _envelope)
    @ns.response(400, "Business rule violation", _envelope)
    @jwt_required()
    @require_system_admin
    def delete(self, user_id):
        """Deactivate a municipal administrator."""
        try:
            data = _svc.update_municipal_administrator(
                user_id=user_id,
                acting_admin_id=int(get_jwt_identity()),
                data={"is_active": False},
            )
            return success_response(data, "Municipal administrator deactivated.")
        except ValueError as exc:
            code = 404 if "not found" in str(exc).lower() else 400
            return error_response(str(exc), status_code=code)


@ns.route("/cities")
class AdminCityListResource(Resource):

    @ns.response(200, "Cities", _envelope)
    @jwt_required()
    @require_system_admin
    def get(self):
        """List all cities. Restricted to system administrators."""
        data = _svc.get_cities()
        return success_response(data, "Cities retrieved.")


@ns.route("/field-workers")
class AdminFieldWorkerListResource(Resource):

    @ns.response(200, "Active field workers", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """List all active field workers for the assignment dropdown."""
        data = _svc.get_field_workers()
        return success_response(data, "Field workers retrieved.")


@ns.route("/dashboard")
class AdminDashboardResource(Resource):

    @ns.response(200, "Dashboard summary", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Get dashboard data for the current administrator subtype."""
        admin_user = _current_admin_user()
        if not admin_user:
            return error_response("User not found.", status_code=404)
        data = _svc.get_dashboard_summary(admin_user)
        return success_response(data, "Dashboard data retrieved.")
