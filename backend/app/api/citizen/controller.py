"""
Citizen controller — complaint submission, tracking, editing, and feedback.

All endpoints require a valid JWT; role check enforces citizen-only access.
Covered Jira stories: TPS-70, TPS-71, TPS-72, TPS-73, TPS-74, TPS-75, TPS-77
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity

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
        enum=["pothole", "streetlight", "drainage", "garbage", "road_damage", "other"],
    ),
    "priority": fields.String(example="medium",
                              enum=["low", "medium", "high", "urgent"]),
    "latitude": fields.Float(example=12.9716),
    "longitude": fields.Float(example=77.5946),
    "address": fields.String(example="MG Road, Bengaluru"),
    "image_url": fields.String(example="https://example.com/photo.jpg"),
})

_complaint_update = ns.model("ComplaintUpdate", {
    "title": fields.String,
    "description": fields.String,
    "category": fields.String,
    "address": fields.String,
    "image_url": fields.String,
    "latitude": fields.Float,
    "longitude": fields.Float,
})

_feedback_create = ns.model("FeedbackCreate", {
    "rating": fields.Integer(required=True, min=1, max=5, example=4),
    "comment": fields.String(example="Repair was done quickly!"),
})


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

    @ns.expect(_complaint_create)
    @ns.response(201, "Complaint submitted", _envelope)
    @ns.response(422, "Validation error", _envelope)
    @jwt_required()
    @require_citizen
    @validate_body(ComplaintCreateSchema)
    def post(self, body):
        """Submit a new civic complaint (TPS-70)."""
        citizen_id = int(get_jwt_identity())
        data = _svc.submit_complaint(citizen_id, body)
        return success_response(data, "Complaint submitted successfully.", 201)


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
            _svc.cancel_complaint(complaint_id, citizen_id)
            return success_response(None, "Complaint cancelled successfully.")
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
