"""
Citizen controller — complaint submission, tracking, editing, and feedback.

All endpoints require a valid JWT; role check enforces citizen-only access.
Covered Jira stories: TPS-70, TPS-71, TPS-72, TPS-73, TPS-74, TPS-75, TPS-77
"""

import os
from uuid import uuid4

from flask import request
from flask import current_app, send_from_directory
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.api.citizen.schema import (
    ComplaintCreateSchema,
    ComplaintUpdateSchema,
    FeedbackCreateSchema,
)
from app.api.citizen.service import CitizenService
from app.utils.decorators import validate_body, require_citizen
from app.utils.responses import success_response, error_response, paginated_response

ns = Namespace("citizen", description="Citizen complaint operations", path="/citizen")
_svc = CitizenService()

# ── Swagger models (docs only) ────────────────────────────────────────────

_envelope = ns.model("CitizenEnvelope", {
    "success": fields.Boolean,
    "message": fields.String,
    "data": fields.Raw,
    "errors": fields.Raw,
})

_complaint_create = ns.model("ComplaintCreate", {
    "title": fields.String(required=True, example="Large pothole on MG Road"),
    "description": fields.String(required=True, example="Deep pothole causing damage"),
    "category": fields.String(
        required=True, example="pothole",
        enum=["pothole"],
    ),
    "priority": fields.String(example="medium",
                              enum=["low", "medium", "high", "urgent"]),
    "latitude": fields.Float(example=12.9716),
    "longitude": fields.Float(example=77.5946),
    "address": fields.String(example="MG Road, Bengaluru"),
    "image_url": fields.String(required=True, example="/api/v1/citizen/complaints/media/photo.jpg"),
    "pincode": fields.String(example="560001"),
    "city_id": fields.Integer(example=42),
})

_complaint_update = ns.model("ComplaintUpdate", {
    "title": fields.String,
    "description": fields.String,
    "category": fields.String,
    "address": fields.String,
    "image_url": fields.String,
    "latitude": fields.Float,
    "longitude": fields.Float,
    "pincode": fields.String,
    "city_id": fields.Integer,
})

_feedback_create = ns.model("FeedbackCreate", {
    "rating": fields.Integer(required=True, min=1, max=5, example=4),
    "comment": fields.String(example="Repair was done quickly!"),
})


def _complaint_media_dir() -> str:
    directory = os.path.join(current_app.instance_path, "uploads", "complaints")
    os.makedirs(directory, exist_ok=True)
    return directory


# ── Endpoints ─────────────────────────────────────────────────────────────

@ns.route("/complaints")
class CitizenComplaintListResource(Resource):

    @ns.response(200, "Paginated complaint list", _envelope)
    @ns.response(401, "Unauthorised")
    @jwt_required()
    @require_citizen
    def get(self):
        """List all complaints submitted by the authenticated citizen (TPS-72).

        Query params: page, per_page, status.
        """
        citizen_id = int(get_jwt_identity())
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status")

        try:
            result = _svc.get_my_complaints(citizen_id, page, per_page, status)
            return paginated_response(
                result["items"], result["total"],
                result["page"], result["per_page"],
                "Complaints retrieved.",
            )
        except ValueError as exc:
            return error_response(str(exc), status_code=400)


@ns.route("/complaints")
class CitizenComplaintCreateResource(Resource):

    @ns.expect(_complaint_create)
    @ns.response(201, "Complaint submitted", _envelope)
    @ns.response(422, "Validation error", _envelope)
    @jwt_required()
    @require_citizen
    @validate_body(ComplaintCreateSchema)
    def post(self, body):
        """Submit a new pothole complaint (TPS-70)."""
        citizen_id = int(get_jwt_identity())
        data = _svc.submit_complaint(citizen_id, body)
        return success_response(data, "Complaint submitted successfully.", 201)


@ns.route("/complaints/media")
class CitizenComplaintMediaUploadResource(Resource):

    @ns.response(201, "Complaint photo uploaded", _envelope)
    @ns.response(400, "Invalid photo upload", _envelope)
    @jwt_required()
    @require_citizen
    def post(self):
        """Upload a complaint photo from a mobile camera or gallery."""
        photo = request.files.get("photo")
        if not photo or not photo.filename:
            return error_response("A photo file is required.", status_code=400)

        if not (photo.mimetype or "").startswith("image/"):
            return error_response("Please upload a valid image file.", status_code=400)

        original_name = secure_filename(photo.filename)
        _, extension = os.path.splitext(original_name)
        extension = extension.lower() if extension else ".jpg"
        filename = f"{uuid4().hex}{extension}"
        file_path = os.path.join(_complaint_media_dir(), filename)
        photo.save(file_path)

        return success_response(
            {
                "filename": filename,
                "image_url": f"/api/v1/citizen/complaints/media/{filename}",
            },
            "Complaint photo uploaded successfully.",
            201,
        )


@ns.route("/complaints/media/<string:filename>")
@ns.param("filename", "Uploaded complaint photo filename")
class CitizenComplaintMediaResource(Resource):

    @ns.response(200, "Complaint photo")
    def get(self, filename):
        """Serve an uploaded complaint photo."""
        return send_from_directory(_complaint_media_dir(), filename)


@ns.route("/complaints/<int:complaint_id>")
@ns.param("complaint_id", "Complaint ID")
class CitizenComplaintResource(Resource):

    @ns.response(200, "Complaint details", _envelope)
    @ns.response(404, "Not found", _envelope)
    @jwt_required()
    @require_citizen
    def get(self, complaint_id):
        """Get a specific complaint owned by the citizen (TPS-73)."""
        citizen_id = int(get_jwt_identity())
        try:
            data = _svc.get_complaint(complaint_id, citizen_id)
            return success_response(data, "Complaint retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=404)

    @ns.expect(_complaint_update)
    @ns.response(200, "Complaint updated", _envelope)
    @ns.response(400, "Cannot edit — not pending", _envelope)
    @ns.response(422, "Validation error", _envelope)
    @jwt_required()
    @require_citizen
    @validate_body(ComplaintUpdateSchema)
    def put(self, body, complaint_id):
        """Edit a pending complaint before it is assigned (TPS-74)."""
        citizen_id = int(get_jwt_identity())
        try:
            data = _svc.update_complaint(complaint_id, citizen_id, body)
            return success_response(data, "Complaint updated successfully.")
        except ValueError as exc:
            code = 404 if "not found" in str(exc).lower() else 400
            return error_response(str(exc), status_code=code)

    @ns.response(200, "Complaint cancelled", _envelope)
    @ns.response(400, "Cannot cancel — not pending", _envelope)
    @ns.response(404, "Not found", _envelope)
    @jwt_required()
    @require_citizen
    def delete(self, complaint_id):
        """Cancel a pending complaint (TPS-75)."""
        citizen_id = int(get_jwt_identity())
        try:
            data = _svc.cancel_complaint(complaint_id, citizen_id)
            return success_response(data, "Complaint cancelled successfully.")
        except ValueError as exc:
            code = 404 if "not found" in str(exc).lower() else 400
            return error_response(str(exc), status_code=code)


@ns.route("/complaints/<int:complaint_id>/feedback")
@ns.param("complaint_id", "Complaint ID")
class CitizenFeedbackResource(Resource):

    @ns.expect(_feedback_create)
    @ns.response(201, "Feedback submitted", _envelope)
    @ns.response(400, "Business rule violation", _envelope)
    @ns.response(422, "Validation error", _envelope)
    @jwt_required()
    @require_citizen
    @validate_body(FeedbackCreateSchema)
    def post(self, body, complaint_id):
        """Submit a rating and comment on a resolved complaint (TPS-77)."""
        citizen_id = int(get_jwt_identity())
        try:
            data = _svc.submit_feedback(complaint_id, citizen_id, body)
            return success_response(data, "Feedback submitted successfully.", 201)
        except ValueError as exc:
            code = 404 if "not found" in str(exc).lower() else 400
            return error_response(str(exc), status_code=code)


@ns.route("/dashboard")
class CitizenDashboardResource(Resource):

    @ns.response(200, "Dashboard summary", _envelope)
    @ns.response(401, "Unauthorised", _envelope)
    @jwt_required()
    @require_citizen
    def get(self):
        """Get complaint counts and recent activity for the citizen dashboard."""
        citizen_id = int(get_jwt_identity())
        data = _svc.get_dashboard_summary(citizen_id)
        return success_response(data, "Dashboard data retrieved.")
