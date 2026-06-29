"""
Citizen controller — complaint submission and tracking endpoints.
"""

from flask_restx import Namespace, Resource, fields

ns = Namespace("citizen", description="Citizen operations", path="/citizen")

# ── Models ─────────────────────────────────────────────────────────────────

complaint_create_model = ns.model(
    "ComplaintCreate",
    {
        "title": fields.String(required=True),
        "description": fields.String(required=True),
        "category": fields.String(required=True),
        "priority": fields.String(default="medium"),
        "latitude": fields.Float(),
        "longitude": fields.Float(),
        "address": fields.String(),
        "image_url": fields.String(),
    },
)

feedback_model = ns.model(
    "FeedbackCreate",
    {
        "rating": fields.Integer(required=True, min=1, max=5),
        "comment": fields.String(),
    },
)


# ── Endpoints ──────────────────────────────────────────────────────────────

@ns.route("/complaints")
class CitizenComplaintListResource(Resource):
    @ns.response(200, "List of citizen's complaints")
    @ns.response(401, "Unauthorised")
    def get(self):
        """Get all complaints submitted by the current citizen."""
        # TODO: implement via CitizenService
        return {"success": True, "message": "Not yet implemented", "data": []}, 501

    @ns.expect(complaint_create_model, validate=True)
    @ns.response(201, "Complaint submitted successfully")
    @ns.response(400, "Validation error")
    def post(self):
        """Submit a new civic complaint."""
        # TODO: implement via CitizenService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501


@ns.route("/complaints/<int:complaint_id>")
@ns.param("complaint_id", "The complaint identifier")
class CitizenComplaintResource(Resource):
    @ns.response(200, "Complaint details")
    @ns.response(404, "Complaint not found")
    def get(self, complaint_id: int):
        """Get details of a specific complaint."""
        # TODO: implement via CitizenService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501

    @ns.response(200, "Complaint updated")
    @ns.response(403, "Forbidden")
    @ns.response(404, "Complaint not found")
    def put(self, complaint_id: int):
        """Update a pending complaint (before assignment)."""
        # TODO: implement via CitizenService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501

    @ns.response(204, "Complaint deleted")
    @ns.response(403, "Forbidden")
    @ns.response(404, "Complaint not found")
    def delete(self, complaint_id: int):
        """Delete a pending complaint."""
        # TODO: implement via CitizenService
        return {"success": True, "message": "Not yet implemented"}, 501


@ns.route("/complaints/<int:complaint_id>/feedback")
@ns.param("complaint_id", "The complaint identifier")
class CitizenFeedbackResource(Resource):
    @ns.expect(feedback_model, validate=True)
    @ns.response(201, "Feedback submitted")
    @ns.response(400, "Validation error")
    @ns.response(404, "Complaint not found")
    def post(self, complaint_id: int):
        """Submit feedback for a resolved complaint."""
        # TODO: implement via CitizenService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501


@ns.route("/dashboard")
class CitizenDashboardResource(Resource):
    @ns.response(200, "Citizen dashboard summary")
    def get(self):
        """Get dashboard summary statistics for the current citizen."""
        # TODO: implement via CitizenService
        return {"success": True, "message": "Not yet implemented", "data": {}}, 501
