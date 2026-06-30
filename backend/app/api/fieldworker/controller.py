"""
Field Worker controller — assignment tracking and progress updates.

All endpoints require field_worker role.
Covered Jira stories: TPS-86, TPS-87, TPS-88, TPS-89, TPS-90
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.fieldworker.schema import FieldWorkerProgressSchema
from app.api.fieldworker.service import FieldWorkerService
from app.utils.decorators import validate_body, require_field_worker
from app.utils.responses import success_response, error_response, paginated_response

ns = Namespace(
    "fieldworker", description="Field Worker operations", path="/fieldworker"
)
_svc = FieldWorkerService()

# ── Swagger models (docs only) ────────────────────────────────────────────

_envelope = ns.model("FWEnvelope", {
    "success": fields.Boolean,
    "message": fields.String,
    "data": fields.Raw,
    "errors": fields.Raw,
})

_progress_update = ns.model("FieldWorkerProgressUpdate", {
    "status": fields.String(
        required=True, example="in_progress",
        enum=["in_progress", "rejected"],
    ),
    "notes": fields.String(example="Pothole marked, materials ordered."),
})


# ── Endpoints ─────────────────────────────────────────────────────────────

@ns.route("/assignments")
class FieldWorkerAssignmentListResource(Resource):

    @ns.response(200, "Paginated assignment list", _envelope)
    @ns.response(401, "Unauthorised")
    @jwt_required()
    @require_field_worker
    def get(self):
        """List all assignments for the authenticated field worker (TPS-86).

        Query params: page, per_page, status.
        """
        worker_id = int(get_jwt_identity())
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status")

        try:
            result = _svc.get_assignments(worker_id, page, per_page, status)
            return paginated_response(
                result["items"], result["total"],
                result["page"], result["per_page"],
                "Assignments retrieved.",
            )
        except ValueError as exc:
            return error_response(str(exc), status_code=400)


@ns.route("/assignments/<int:assignment_id>")
@ns.param("assignment_id", "Assignment ID")
class FieldWorkerAssignmentResource(Resource):

    @ns.response(200, "Assignment details", _envelope)
    @ns.response(404, "Not found", _envelope)
    @jwt_required()
    @require_field_worker
    def get(self, assignment_id):
        """Get full details of a specific assignment (TPS-87)."""
        worker_id = int(get_jwt_identity())
        try:
            data = _svc.get_assignment(assignment_id, worker_id)
            return success_response(data, "Assignment retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=404)

    @ns.expect(_progress_update)
    @ns.response(200, "Progress updated", _envelope)
    @ns.response(400, "Invalid transition", _envelope)
    @ns.response(422, "Validation error", _envelope)
    @jwt_required()
    @require_field_worker
    @validate_body(FieldWorkerProgressSchema)
    def put(self, body, assignment_id):
        """Update assignment progress (in_progress or rejected) (TPS-89)."""
        worker_id = int(get_jwt_identity())
        try:
            data = _svc.update_progress(assignment_id, worker_id, body)
            return success_response(data, "Progress updated successfully.")
        except ValueError as exc:
            code = 404 if "not found" in str(exc).lower() else 400
            return error_response(str(exc), status_code=code)


@ns.route("/assignments/<int:assignment_id>/accept")
@ns.param("assignment_id", "Assignment ID")
class FieldWorkerAcceptResource(Resource):

    @ns.response(200, "Assignment accepted", _envelope)
    @ns.response(400, "Invalid transition", _envelope)
    @ns.response(404, "Not found", _envelope)
    @jwt_required()
    @require_field_worker
    def post(self, assignment_id):
        """Accept an assigned task (TPS-88)."""
        worker_id = int(get_jwt_identity())
        try:
            data = _svc.accept_assignment(assignment_id, worker_id)
            return success_response(data, "Assignment accepted.")
        except ValueError as exc:
            code = 404 if "not found" in str(exc).lower() else 400
            return error_response(str(exc), status_code=code)


@ns.route("/assignments/<int:assignment_id>/complete")
@ns.param("assignment_id", "Assignment ID")
class FieldWorkerCompleteResource(Resource):

    @ns.response(200, "Assignment completed", _envelope)
    @ns.response(400, "Invalid transition", _envelope)
    @ns.response(404, "Not found", _envelope)
    @jwt_required()
    @require_field_worker
    def post(self, assignment_id):
        """Mark a task as completed (TPS-90)."""
        worker_id = int(get_jwt_identity())
        try:
            data = _svc.complete_assignment(assignment_id, worker_id)
            return success_response(data, "Assignment marked as completed.")
        except ValueError as exc:
            code = 404 if "not found" in str(exc).lower() else 400
            return error_response(str(exc), status_code=code)


@ns.route("/dashboard")
class FieldWorkerDashboardResource(Resource):

    @ns.response(200, "Dashboard summary", _envelope)
    @ns.response(401, "Unauthorised")
    @jwt_required()
    @require_field_worker
    def get(self):
        """Get assignment counts and recent tasks for the field worker dashboard."""
        worker_id = int(get_jwt_identity())
        data = _svc.get_dashboard_summary(worker_id)
        return success_response(data, "Dashboard data retrieved.")
