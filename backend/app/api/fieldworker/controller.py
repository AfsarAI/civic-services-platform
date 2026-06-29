"""
Field Worker controller — task management and progress update endpoints.
"""

from flask_restx import Namespace, Resource, fields

ns = Namespace("fieldworker", description="Field Worker operations", path="/fieldworker")

# ── Models ─────────────────────────────────────────────────────────────────

progress_update_model = ns.model(
    "ProgressUpdate",
    {
        "status": fields.String(required=True, description="New assignment status"),
        "notes": fields.String(description="Progress notes"),
        "image_url": fields.String(description="Evidence photo URL"),
    },
)


# ── Endpoints ──────────────────────────────────────────────────────────────

@ns.route("/assignments")
class FieldWorkerAssignmentListResource(Resource):
    @ns.response(200, "List of assigned tasks")
    @ns.response(401, "Unauthorised")
    def get(self):
        """Get all tasks assigned to the current field worker."""
        # TODO: implement via FieldWorkerService
        return {"success": True, "message": "Not yet implemented", "data": []}, 501


@ns.route("/assignments/<int:assignment_id>")
@ns.param("assignment_id", "The assignment identifier")
class FieldWorkerAssignmentResource(Resource):
    @ns.response(200, "Assignment details")
    @ns.response(404, "Not found")
    def get(self, assignment_id: int):
        """Get details of a specific assignment."""
        # TODO: implement via FieldWorkerService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501

    @ns.expect(progress_update_model, validate=True)
    @ns.response(200, "Progress updated")
    @ns.response(403, "Forbidden")
    @ns.response(404, "Not found")
    def put(self, assignment_id: int):
        """Update repair progress for an assignment."""
        # TODO: implement via FieldWorkerService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501


@ns.route("/assignments/<int:assignment_id>/accept")
@ns.param("assignment_id", "The assignment identifier")
class FieldWorkerAcceptResource(Resource):
    @ns.response(200, "Assignment accepted")
    def post(self, assignment_id: int):
        """Accept an assigned task."""
        # TODO: implement via FieldWorkerService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501


@ns.route("/assignments/<int:assignment_id>/complete")
@ns.param("assignment_id", "The assignment identifier")
class FieldWorkerCompleteResource(Resource):
    @ns.response(200, "Assignment marked as complete")
    def post(self, assignment_id: int):
        """Mark a task as completed."""
        # TODO: implement via FieldWorkerService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501


@ns.route("/dashboard")
class FieldWorkerDashboardResource(Resource):
    @ns.response(200, "Field worker dashboard summary")
    def get(self):
        """Get dashboard summary for the current field worker."""
        # TODO: implement via FieldWorkerService
        return {"success": True, "message": "Not yet implemented", "data": {}}, 501
