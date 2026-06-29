"""
Administrator controller — complaint management, user management, assignments.
"""

from flask_restx import Namespace, Resource, fields

ns = Namespace("admin", description="Administrator operations", path="/admin")

# ── Models ─────────────────────────────────────────────────────────────────

assign_model = ns.model(
    "AssignComplaint",
    {
        "worker_id": fields.Integer(required=True, description="Field worker user ID"),
        "notes": fields.String(description="Assignment notes"),
    },
)

status_update_model = ns.model(
    "UpdateComplaintStatus",
    {
        "status": fields.String(required=True),
        "notes": fields.String(),
    },
)

user_update_model = ns.model(
    "UpdateUser",
    {
        "is_active": fields.Boolean(),
        "role_id": fields.Integer(),
    },
)


# ── Complaint Management ───────────────────────────────────────────────────

@ns.route("/complaints")
class AdminComplaintListResource(Resource):
    @ns.response(200, "All complaints")
    def get(self):
        """Get all complaints with optional filters (status, category, priority)."""
        # TODO: implement via AdminService
        return {"success": True, "message": "Not yet implemented", "data": []}, 501


@ns.route("/complaints/<int:complaint_id>")
@ns.param("complaint_id", "The complaint identifier")
class AdminComplaintResource(Resource):
    @ns.response(200, "Complaint details")
    @ns.response(404, "Not found")
    def get(self, complaint_id: int):
        """Get full details of any complaint."""
        # TODO: implement via AdminService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501

    @ns.expect(status_update_model)
    @ns.response(200, "Status updated")
    def put(self, complaint_id: int):
        """Update complaint status or priority."""
        # TODO: implement via AdminService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501


@ns.route("/complaints/<int:complaint_id>/assign")
@ns.param("complaint_id", "The complaint identifier")
class AdminAssignComplaintResource(Resource):
    @ns.expect(assign_model, validate=True)
    @ns.response(201, "Complaint assigned successfully")
    @ns.response(404, "Complaint or worker not found")
    def post(self, complaint_id: int):
        """Assign a complaint to a field worker."""
        # TODO: implement via AdminService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501


# ── User Management ────────────────────────────────────────────────────────

@ns.route("/users")
class AdminUserListResource(Resource):
    @ns.response(200, "All users")
    def get(self):
        """Get all platform users."""
        # TODO: implement via AdminService
        return {"success": True, "message": "Not yet implemented", "data": []}, 501


@ns.route("/users/<int:user_id>")
@ns.param("user_id", "The user identifier")
class AdminUserResource(Resource):
    @ns.response(200, "User details")
    def get(self, user_id: int):
        """Get user details."""
        # TODO: implement via AdminService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501

    @ns.expect(user_update_model)
    @ns.response(200, "User updated")
    def put(self, user_id: int):
        """Update a user's status or role."""
        # TODO: implement via AdminService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501


# ── Dashboard ──────────────────────────────────────────────────────────────

@ns.route("/dashboard")
class AdminDashboardResource(Resource):
    @ns.response(200, "Admin dashboard summary")
    def get(self):
        """Get administrator dashboard statistics."""
        # TODO: implement via AdminService
        return {"success": True, "message": "Not yet implemented", "data": {}}, 501


@ns.route("/field-workers")
class AdminFieldWorkerListResource(Resource):
    @ns.response(200, "List of field workers")
    def get(self):
        """Get all field workers (for assignment dropdown)."""
        # TODO: implement via AdminService
        return {"success": True, "message": "Not yet implemented", "data": []}, 501
