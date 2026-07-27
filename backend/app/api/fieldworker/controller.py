"""
Field Worker controller — assignment tracking and progress updates.

All endpoints require field_worker role.
Covered Jira stories: TPS-86, TPS-87, TPS-88, TPS-89, TPS-90
"""

import os
from uuid import uuid4

from flask import request
from flask import current_app, send_from_directory
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

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

_complete_body = ns.model("FieldWorkerCompleteBody", {
    "evidence_url": fields.String(
        example="/api/v1/fieldworker/assignments/media/photo.jpg",
        description="Optional URL returned by POST /fieldworker/assignments/media",
    ),
})


def _assignment_media_dir() -> str:
    directory = os.path.join(current_app.instance_path, "uploads", "assignments")
    os.makedirs(directory, exist_ok=True)
    return directory


# ── Endpoints ─────────────────────────────────────────────────────────────

@ns.route("/assignments")
class FieldWorkerAssignmentListResource(Resource):

    @ns.response(200, "Paginated assignment list", _envelope)
    @ns.response(401, "Unauthorised")
    @jwt_required()
    @require_field_worker
    def get(self):
        """List all assignments for the authenticated field worker (TPS-86).

        Query params: page, per_page, status, priority, search, sort_by
        (``assigned_at`` default or ``priority``), sort_order (``asc``/``desc``).
        """
        worker_id = int(get_jwt_identity())
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status")
        priority = request.args.get("priority")
        search = request.args.get("search")
        sort_by = request.args.get("sort_by", "assigned_at")
        sort_order = request.args.get("sort_order", "desc")

        try:
            result = _svc.get_assignments(
                worker_id, page, per_page, status, priority, search, sort_by, sort_order
            )
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

    @ns.expect(_complete_body)
    @ns.response(200, "Assignment completed", _envelope)
    @ns.response(400, "Invalid transition", _envelope)
    @ns.response(404, "Not found", _envelope)
    @jwt_required()
    @require_field_worker
    def post(self, assignment_id):
        """Mark a task as completed, optionally attaching photo evidence (TPS-90).

        Body is optional JSON: ``{"evidence_url": "..."}``. Upload the photo
        first via ``POST /fieldworker/assignments/media`` to obtain the URL.
        """
        worker_id = int(get_jwt_identity())
        body = {}
        if request.data:
            try:
                body = request.get_json() or {}
            except Exception:
                return error_response("Invalid JSON body.", status_code=400)
        evidence_url = body.get("evidence_url")
        try:
            data = _svc.complete_assignment(assignment_id, worker_id, evidence_url)
            return success_response(data, "Assignment marked as completed.")
        except ValueError as exc:
            code = 404 if "not found" in str(exc).lower() else 400
            return error_response(str(exc), status_code=code)


@ns.route("/assignments/media")
class FieldWorkerAssignmentMediaUploadResource(Resource):

    @ns.response(201, "Evidence photo uploaded", _envelope)
    @ns.response(400, "Invalid photo upload", _envelope)
    @jwt_required()
    @require_field_worker
    def post(self):
        """Upload a repair-completion evidence photo from a mobile camera or gallery."""
        photo = request.files.get("photo")
        if not photo or not photo.filename:
            return error_response("A photo file is required.", status_code=400)

        if not (photo.mimetype or "").startswith("image/"):
            return error_response("Please upload a valid image file.", status_code=400)

        original_name = secure_filename(photo.filename)
        _, extension = os.path.splitext(original_name)
        extension = (extension or ".jpg").lower()
        if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
            extension = ".jpg"
        filename = f"{uuid4().hex}{extension}"
        file_path = os.path.join(_assignment_media_dir(), filename)
        photo.save(file_path)

        return success_response(
            {
                "filename": filename,
                "evidence_url": f"/api/v1/fieldworker/assignments/media/{filename}",
            },
            "Evidence photo uploaded successfully.",
            201,
        )


@ns.route("/assignments/media/<string:filename>")
@ns.param("filename", "Uploaded evidence photo filename")
class FieldWorkerAssignmentMediaResource(Resource):

    @ns.response(200, "Evidence photo")
    def get(self, filename):
        """Serve an uploaded evidence photo."""
        return send_from_directory(_assignment_media_dir(), filename)


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
