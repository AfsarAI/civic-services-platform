"""
Reports controller — statistical analytics endpoints (admin-only).

Covered Jira stories: TPS-85, TPS-96, TPS-97, TPS-98

Accessible to both administrator subtypes: system administrators see
platform-wide (unscoped) figures, municipal administrators are automatically
scoped to their own city — mirroring the same pattern used for
``/admin/complaints``/``/admin/field-workers``.
"""

from flask import request, Response
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.api.reports.service import ReportsService
from app.models.user import User
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


def _current_admin_user() -> User:
    return User.query.get(int(get_jwt_identity()))


def _scoped_city_id(admin_user: User) -> int | None:
    """Return the admin's city ID when they are a municipal administrator.

    ``None`` means unscoped (system administrators see every city).
    """
    return admin_user.admin_city_id if admin_user.is_municipal_admin else None


def _parse_date_filters():
    """Parse the shared ``date_from``/``date_to`` query params.

    Raises:
        ValueError: If either date string is malformed.
    """
    date_from = _svc.parse_date(request.args.get("date_from"))
    date_to = _svc.parse_date(request.args.get("date_to"), end_of_day=True)
    return date_from, date_to


# ── Endpoints ─────────────────────────────────────────────────────────────

@ns.route("/complaints/summary")
class ComplaintSummaryReport(Resource):

    @ns.response(200, "Complaint summary", _envelope)
    @ns.response(400, "Invalid filter", _envelope)
    @ns.response(403, "Forbidden", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Overall complaint statistics: totals, status breakdown, avg resolution time (TPS-85).

        Municipal administrators see only their own city's figures.
        Query params: ``date_from``, ``date_to`` (YYYY-MM-DD), ``status``.
        """
        city_id = _scoped_city_id(_current_admin_user())
        status = request.args.get("status")
        try:
            date_from, date_to = _parse_date_filters()
            data = _svc.get_complaint_summary(city_id, date_from, date_to, status)
            return success_response(data, "Complaint summary retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=400)


@ns.route("/complaints/by-status")
class ComplaintsByStatusReport(Resource):

    @ns.response(200, "Complaints by status", _envelope)
    @ns.response(400, "Invalid filter", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Complaint counts and percentages grouped by status (TPS-96).

        Query params: ``date_from``, ``date_to`` (YYYY-MM-DD).
        """
        city_id = _scoped_city_id(_current_admin_user())
        try:
            date_from, date_to = _parse_date_filters()
            data = _svc.get_complaints_by_status(city_id, date_from, date_to)
            return success_response(data, "Complaints by status retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=400)


@ns.route("/complaints/by-category")
class ComplaintsByCategoryReport(Resource):

    @ns.response(200, "Complaints by category", _envelope)
    @ns.response(400, "Invalid filter", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Complaint counts and percentages grouped by category (TPS-97).

        Query params: ``date_from``, ``date_to`` (YYYY-MM-DD), ``status``.
        """
        city_id = _scoped_city_id(_current_admin_user())
        status = request.args.get("status")
        try:
            date_from, date_to = _parse_date_filters()
            data = _svc.get_complaints_by_category(city_id, date_from, date_to, status)
            return success_response(data, "Complaints by category retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=400)


@ns.route("/complaints/by-priority")
class ComplaintsByPriorityReport(Resource):

    @ns.response(200, "Complaints by priority", _envelope)
    @ns.response(400, "Invalid filter", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Complaint counts and percentages grouped by priority.

        Query params: ``date_from``, ``date_to`` (YYYY-MM-DD), ``status``.
        """
        city_id = _scoped_city_id(_current_admin_user())
        status = request.args.get("status")
        try:
            date_from, date_to = _parse_date_filters()
            data = _svc.get_complaints_by_priority(city_id, date_from, date_to, status)
            return success_response(data, "Complaints by priority retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=400)


@ns.route("/complaints/by-location")
class ComplaintsByLocationReport(Resource):

    @ns.response(200, "Complaints by location", _envelope)
    @ns.response(400, "Invalid filter", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Complaint counts and percentages grouped by city.

        A municipal administrator is already scoped to a single city, so this
        naturally returns one row for them; system administrators see every
        city. Query params: ``date_from``, ``date_to`` (YYYY-MM-DD), ``status``.
        """
        city_id = _scoped_city_id(_current_admin_user())
        status = request.args.get("status")
        try:
            date_from, date_to = _parse_date_filters()
            data = _svc.get_complaints_by_location(city_id, date_from, date_to, status)
            return success_response(data, "Complaints by location retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=400)


@ns.route("/complaints/trends")
class ComplaintTrendsReport(Resource):

    @ns.response(200, "Complaint trends", _envelope)
    @ns.response(400, "Invalid period or filter", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Complaint submission trends over time (TPS-98).

        Query params: ``period`` — one of ``daily`` (default), ``weekly``, ``monthly``;
        ``date_from``, ``date_to`` (YYYY-MM-DD, overrides the default window); ``status``.
        """
        city_id = _scoped_city_id(_current_admin_user())
        period = request.args.get("period", "daily")
        status = request.args.get("status")
        try:
            date_from, date_to = _parse_date_filters()
            data = _svc.get_complaint_trends(period, city_id, date_from, date_to, status)
            return success_response(data, "Complaint trends retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=400)


@ns.route("/workers/performance")
class WorkerPerformanceReport(Resource):

    @ns.response(200, "Worker performance metrics", _envelope)
    @ns.response(400, "Invalid filter", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Field worker performance: assignment counts, completion rate, avg time.

        Municipal administrators only see field workers belonging to their
        own city. Query params: ``date_from``, ``date_to`` (YYYY-MM-DD).
        """
        city_id = _scoped_city_id(_current_admin_user())
        try:
            date_from, date_to = _parse_date_filters()
            data = _svc.get_worker_performance(city_id, date_from, date_to)
            return success_response(data, "Worker performance retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=400)


def _export_filename(extension: str) -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    return f"complaint-report-{stamp}.{extension}"


@ns.route("/export/csv")
class ExportCsvReport(Resource):

    @ns.response(200, "CSV file")
    @ns.response(400, "Invalid filter", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Export the current filtered report data as a CSV file.

        Query params: ``date_from``, ``date_to`` (YYYY-MM-DD), ``status``.
        """
        city_id = _scoped_city_id(_current_admin_user())
        status = request.args.get("status")
        try:
            date_from, date_to = _parse_date_filters()
            dataset = _svc.build_export_dataset(city_id, date_from, date_to, status)
            csv_text = _svc.export_csv(dataset)
        except ValueError as exc:
            return error_response(str(exc), status_code=400)

        return Response(
            csv_text,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={_export_filename('csv')}"
            },
        )


@ns.route("/export/excel")
class ExportExcelReport(Resource):

    @ns.response(200, "Excel file")
    @ns.response(400, "Invalid filter", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Export the current filtered report data as an XLSX workbook.

        Query params: ``date_from``, ``date_to`` (YYYY-MM-DD), ``status``.
        """
        city_id = _scoped_city_id(_current_admin_user())
        status = request.args.get("status")
        try:
            date_from, date_to = _parse_date_filters()
            dataset = _svc.build_export_dataset(city_id, date_from, date_to, status)
            xlsx_bytes = _svc.export_excel(dataset)
        except ValueError as exc:
            return error_response(str(exc), status_code=400)

        return Response(
            xlsx_bytes,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={_export_filename('xlsx')}"
            },
        )


@ns.route("/export/pdf")
class ExportPdfReport(Resource):

    @ns.response(200, "PDF file")
    @ns.response(400, "Invalid filter", _envelope)
    @jwt_required()
    @require_admin
    def get(self):
        """Export the current filtered report data as a PDF document.

        Query params: ``date_from``, ``date_to`` (YYYY-MM-DD), ``status``.
        """
        city_id = _scoped_city_id(_current_admin_user())
        status = request.args.get("status")
        try:
            date_from, date_to = _parse_date_filters()
            dataset = _svc.build_export_dataset(city_id, date_from, date_to, status)
            pdf_bytes = _svc.export_pdf(dataset)
        except ValueError as exc:
            return error_response(str(exc), status_code=400)

        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={_export_filename('pdf')}"
            },
        )
