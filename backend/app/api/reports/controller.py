"""
Reports controller — statistical analytics endpoints (admin-only).

Covered Jira stories: TPS-85, TPS-96, TPS-97, TPS-98
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required

from app.api.reports.service import ReportsService
from app.utils.decorators import require_admin
from app.utils.responses import success_response, error_response

ns = Namespace("reports", description="Reports and analytics", path="/reports")
_svc = ReportsService()

# ── Swagger models (docs only) ────────────────────────────────────────────

_envelope = ns.model("ReportsEnvelope", {
    "success": fields.Boolean,
    "message": fields.String,
    "data": fields.Raw,
    "errors": fields.Raw,
})


# ── Endpoints ─────────────────────────────────────────────────────────────

@ns.route("/complaints/summary")
class ComplaintSummaryReport(Resource):

    @ns.response(200, "Complaint summary", _envelope)
    @ns.response(403, "Forbidden", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Overall complaint statistics: totals, status breakdown, avg resolution time (TPS-85)."""
        data = _svc.get_complaint_summary()
        return success_response(data, "Complaint summary retrieved.")


@ns.route("/complaints/by-status")
class ComplaintsByStatusReport(Resource):

    @ns.response(200, "Complaints by status", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Complaint counts and percentages grouped by status (TPS-96)."""
        data = _svc.get_complaints_by_status()
        return success_response(data, "Complaints by status retrieved.")


@ns.route("/complaints/by-category")
class ComplaintsByCategoryReport(Resource):

    @ns.response(200, "Complaints by category", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Complaint counts and percentages grouped by category (TPS-97)."""
        data = _svc.get_complaints_by_category()
        return success_response(data, "Complaints by category retrieved.")


@ns.route("/complaints/trends")
class ComplaintTrendsReport(Resource):

    @ns.response(200, "Complaint trends", _envelope)
    @ns.response(400, "Invalid period", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Complaint submission trends over time (TPS-98).

        Query param: ``period`` — one of ``daily`` (default), ``weekly``, ``monthly``.
        """
        period = request.args.get("period", "daily")
        try:
            data = _svc.get_complaint_trends(period)
            return success_response(data, "Complaint trends retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=400)


@ns.route("/workers/performance")
class WorkerPerformanceReport(Resource):

    @ns.response(200, "Worker performance metrics", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Field worker performance: assignment counts, completion rate, avg time."""
        data = _svc.get_worker_performance()
        return success_response(data, "Worker performance retrieved.")
