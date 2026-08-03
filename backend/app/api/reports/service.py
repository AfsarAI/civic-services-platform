"""
Reports service — analytics and statistics for the administrator dashboard.

All queries run directly on the database using SQLAlchemy aggregations.
SQLite-compatible: date grouping uses strftime().

Every report accepts an optional ``city_id`` (municipal administrators are
scoped to their own city; ``None`` means unscoped, i.e. system administrators)
plus optional ``date_from``/``date_to``/``status``/``priority`` filters
(TPS-85/96/97/98, AC3/AC4).
"""

from datetime import datetime, timedelta

from sqlalchemy import func

from app.models.city import City
from app.models.complaint import Complaint
from app.models.complaint_assignment import ComplaintAssignment
from app.models.feedback import Feedback
from app.models.role import Role
from app.models.user import User


class ReportsService:
    """Generates statistical reports for administrators."""

    # ── Shared filtering helpers ─────────────────────────────────────────

    @staticmethod
    def parse_date(value: str, end_of_day: bool = False):
        """Parse a ``YYYY-MM-DD`` query param into a ``datetime``.

        Raises:
            ValueError: If ``value`` is not a valid date string.
        """
        if not value:
            return None
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date '{value}'. Use YYYY-MM-DD format.")
        if end_of_day:
            parsed = parsed + timedelta(hours=23, minutes=59, seconds=59)
        return parsed

    VALID_PRIORITIES = ("low", "medium", "high", "urgent")

    @staticmethod
    def _filtered_query(
        city_id: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
        status: str = None,
        priority: str = None,
    ):
        """Return a ``Complaint`` query with the given optional filters applied."""
        query = Complaint.query
        if city_id is not None:
            query = query.filter(Complaint.city_id == city_id)
        if date_from is not None:
            query = query.filter(Complaint.created_at >= date_from)
        if date_to is not None:
            query = query.filter(Complaint.created_at <= date_to)
        if status is not None:
            if status not in Complaint.VALID_STATUSES:
                raise ValueError(f"Invalid status '{status}'.")
            query = query.filter(Complaint.status == status)
        if priority is not None:
            if priority not in ReportsService.VALID_PRIORITIES:
                raise ValueError(
                    f"Invalid priority '{priority}'. "
                    f"Choose from: {', '.join(ReportsService.VALID_PRIORITIES)}."
                )
            query = query.filter(Complaint.priority == priority)
        return query

    # ── Summary ───────────────────────────────────────────────────────────

    def get_complaint_summary(
        self,
        city_id: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
        status: str = None,
        priority: str = None,
    ) -> dict:
        """Overall complaint statistics: totals, resolution rate, avg time."""
        base = self._filtered_query(city_id, date_from, date_to, status, priority)
        total = base.count()

        by_status = {
            s: self._filtered_query(city_id, date_from, date_to).filter(Complaint.status == s).count()
            for s in Complaint.VALID_STATUSES
        }

        by_category = {}
        for row in (
            base.with_entities(Complaint.category, func.count(Complaint.id))
            .group_by(Complaint.category).all()
        ):
            by_category[row[0]] = row[1]

        by_priority = {}
        for row in (
            base.with_entities(Complaint.priority, func.count(Complaint.id))
            .group_by(Complaint.priority).all()
        ):
            by_priority[row[0]] = row[1]

        resolved_count = base.filter(Complaint.resolved_at.isnot(None)).count()

        # Average resolution time in hours (SQLite: julianday diff * 24)
        avg_hours = None
        if resolved_count:
            result = base.filter(Complaint.resolved_at.isnot(None)).with_entities(
                func.avg(
                    (func.julianday(Complaint.resolved_at) -
                     func.julianday(Complaint.created_at)) * 24
                )
            ).scalar()
            if result is not None:
                avg_hours = round(float(result), 1)

        open_count = sum(
            by_status.get(s, 0)
            for s in [
                Complaint.STATUS_PENDING,
                Complaint.STATUS_ASSIGNED,
                Complaint.STATUS_IN_PROGRESS,
            ]
        )

        return {
            "total": total,
            "open": open_count,
            "resolved": resolved_count,
            "resolution_rate": round(resolved_count / total * 100, 1) if total else 0,
            "avg_resolution_hours": avg_hours,
            "by_status": by_status,
            "by_category": by_category,
            "by_priority": by_priority,
        }

    # ── By status ─────────────────────────────────────────────────────────

    def get_complaints_by_status(
        self, city_id: int = None, date_from: datetime = None, date_to: datetime = None,
    ) -> dict:
        """Counts and percentages for each complaint status."""
        base = self._filtered_query(city_id, date_from, date_to)
        total = base.count()
        rows = (
            base.with_entities(Complaint.status, func.count(Complaint.id))
            .group_by(Complaint.status)
            .all()
        )
        data = []
        for status, count in rows:
            data.append({
                "status": status,
                "count": count,
                "percentage": round(count / total * 100, 1) if total else 0,
            })
        data.sort(key=lambda x: Complaint.VALID_STATUSES.index(x["status"])
                  if x["status"] in Complaint.VALID_STATUSES else 99)
        return {"total": total, "breakdown": data}

    # ── By category ───────────────────────────────────────────────────────

    def get_complaints_by_category(
        self,
        city_id: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
        status: str = None,
        priority: str = None,
    ) -> dict:
        """Counts and percentages per complaint category."""
        base = self._filtered_query(city_id, date_from, date_to, status, priority)
        total = base.count()
        rows = (
            base.with_entities(Complaint.category, func.count(Complaint.id))
            .group_by(Complaint.category)
            .order_by(func.count(Complaint.id).desc())
            .all()
        )
        breakdown = [
            {
                "category": cat,
                "count": cnt,
                "percentage": round(cnt / total * 100, 1) if total else 0,
            }
            for cat, cnt in rows
        ]
        return {"total": total, "breakdown": breakdown}

    # ── By priority ───────────────────────────────────────────────────────

    def get_complaints_by_priority(
        self,
        city_id: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
        status: str = None,
        priority: str = None,
    ) -> dict:
        """Counts and percentages per complaint priority."""
        base = self._filtered_query(city_id, date_from, date_to, status, priority)
        total = base.count()
        rows = (
            base.with_entities(Complaint.priority, func.count(Complaint.id))
            .group_by(Complaint.priority)
            .order_by(func.count(Complaint.id).desc())
            .all()
        )
        breakdown = [
            {
                "priority": priority,
                "count": cnt,
                "percentage": round(cnt / total * 100, 1) if total else 0,
            }
            for priority, cnt in rows
        ]
        return {"total": total, "breakdown": breakdown}

    # ── By location ───────────────────────────────────────────────────────

    def get_complaints_by_location(
        self,
        city_id: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
        status: str = None,
        priority: str = None,
    ) -> dict:
        """Counts and percentages per city.

        For a municipal administrator (``city_id`` provided) this naturally
        collapses to a single row for their own city.
        """
        base = self._filtered_query(city_id, date_from, date_to, status, priority)
        total = base.count()
        rows = (
            base.join(City, City.id == Complaint.city_id)
            .with_entities(City.id, City.name, func.count(Complaint.id))
            .group_by(City.id, City.name)
            .order_by(func.count(Complaint.id).desc())
            .all()
        )
        breakdown = [
            {
                "city_id": cid,
                "city_name": name,
                "count": cnt,
                "percentage": round(cnt / total * 100, 1) if total else 0,
            }
            for cid, name, cnt in rows
        ]
        unassigned = total - sum(r["count"] for r in breakdown)
        if unassigned > 0:
            breakdown.append({
                "city_id": None,
                "city_name": "Unassigned",
                "count": unassigned,
                "percentage": round(unassigned / total * 100, 1) if total else 0,
            })
        return {"total": total, "breakdown": breakdown}

    # ── Trends ────────────────────────────────────────────────────────────

    def get_complaint_trends(
        self,
        period: str = "daily",
        city_id: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
        status: str = None,
        priority: str = None,
    ) -> dict:
        """Complaint submission counts grouped by time period.

        Args:
            period: One of ``daily`` (last 30 days), ``weekly`` (last 12 weeks),
                    ``monthly`` (last 12 months) — used only when ``date_from``/
                    ``date_to`` are not supplied.

        Raises:
            ValueError: If period is invalid.
        """
        valid_periods = ("daily", "weekly", "monthly")
        if period not in valid_periods:
            raise ValueError(
                f"Invalid period '{period}'. Choose from: {', '.join(valid_periods)}."
            )

        fmt_map = {
            "daily": "%Y-%m-%d",
            "weekly": "%Y-%W",
            "monthly": "%Y-%m",
        }
        fmt = fmt_map[period]

        base = self._filtered_query(city_id, date_from, date_to, status, priority)
        rows = (
            base.with_entities(
                func.strftime(fmt, Complaint.created_at).label("period"),
                func.count(Complaint.id).label("count"),
            )
            .group_by("period")
            .order_by("period")
            .all()
        )

        trend_data = [{"period": r.period, "count": r.count} for r in rows]

        # Only clip to a fixed recent window when the caller hasn't supplied
        # an explicit date range — an explicit range should be honoured as-is.
        if date_from is None and date_to is None:
            limit = {"daily": 30, "weekly": 12, "monthly": 12}[period]
            trend_data = trend_data[-limit:]

        return {"period": period, "data": trend_data}

    # ── Worker performance ────────────────────────────────────────────────

    def get_worker_performance(
        self,
        city_id: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
    ) -> dict:
        """Per-field-worker assignment statistics.

        Args:
            city_id: When provided (municipal administrators), restricts to
                field workers belonging to that city.
            date_from/date_to: Restrict to assignments made within this range.
        """
        fw_role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
        if not fw_role:
            return {"workers": []}

        worker_query = User.query.filter_by(role_id=fw_role.id)
        if city_id is not None:
            worker_query = worker_query.filter(User.city_id == city_id)
        workers = worker_query.all()
        results = []

        for worker in workers:
            base = ComplaintAssignment.query.filter_by(worker_id=worker.id)
            if date_from is not None:
                base = base.filter(ComplaintAssignment.assigned_at >= date_from)
            if date_to is not None:
                base = base.filter(ComplaintAssignment.assigned_at <= date_to)
            total = base.count()

            by_status = {
                s: base.filter(ComplaintAssignment.status == s).count()
                for s in [
                    ComplaintAssignment.STATUS_ASSIGNED,
                    ComplaintAssignment.STATUS_ACCEPTED,
                    ComplaintAssignment.STATUS_IN_PROGRESS,
                    ComplaintAssignment.STATUS_COMPLETED,
                    ComplaintAssignment.STATUS_REJECTED,
                ]
            }

            # Avg completion time in hours (accepted_at → completed_at)
            avg_completion_hours = None
            completed_with_times = base.filter(
                ComplaintAssignment.status == ComplaintAssignment.STATUS_COMPLETED,
                ComplaintAssignment.accepted_at.isnot(None),
                ComplaintAssignment.completed_at.isnot(None),
            )
            if completed_with_times.count():
                result = completed_with_times.with_entities(
                    func.avg(
                        (func.julianday(ComplaintAssignment.completed_at) -
                         func.julianday(ComplaintAssignment.accepted_at)) * 24
                    )
                ).scalar()
                if result is not None:
                    avg_completion_hours = round(float(result), 1)

            completion_rate = (
                round(by_status[ComplaintAssignment.STATUS_COMPLETED] / total * 100, 1)
                if total else 0
            )

            results.append({
                "worker_id": worker.id,
                "name": worker.full_name,
                "email": worker.email,
                "is_active": worker.is_active,
                "total_assignments": total,
                "by_status": by_status,
                "completion_rate": completion_rate,
                "avg_completion_hours": avg_completion_hours,
            })

        # Sort by total assignments descending
        results.sort(key=lambda x: x["total_assignments"], reverse=True)
        return {"workers": results}

    # ── Citizen feedback summary ─────────────────────────────────────────

    def get_citizen_feedback_summary(
        self,
        city_id: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
    ) -> dict:
        """Aggregate citizen feedback statistics.

        Returns total count, average rating, rating distribution (1-5 stars),
        and the most recent feedback comments.
        """
        base = Feedback.query.join(
            Complaint, Complaint.id == Feedback.complaint_id,
        )
        if city_id is not None:
            base = base.filter(Complaint.city_id == city_id)
        if date_from is not None:
            base = base.filter(Feedback.created_at >= date_from)
        if date_to is not None:
            base = base.filter(Feedback.created_at <= date_to)

        total = base.count()

        avg_rating = None
        if total:
            result = base.with_entities(func.avg(Feedback.rating)).scalar()
            if result is not None:
                avg_rating = round(float(result), 1)

        # Rating distribution: count per star level (1-5)
        distribution = {str(i): 0 for i in range(1, 6)}
        rows = (
            base.with_entities(Feedback.rating, func.count(Feedback.id))
            .group_by(Feedback.rating)
            .all()
        )
        for rating, count in rows:
            distribution[str(rating)] = count

        # Recent feedback (latest 10 comments that are not empty)
        recent = (
            base.filter(Feedback.comment.isnot(None), Feedback.comment != "")
            .order_by(Feedback.created_at.desc())
            .limit(10)
            .all()
        )
        recent_comments = [
            {
                "rating": fb.rating,
                "comment": fb.comment,
                "created_at": fb.created_at.strftime("%Y-%m-%d %H:%M") if fb.created_at else None,
            }
            for fb in recent
        ]

        return {
            "total": total,
            "avg_rating": avg_rating,
            "distribution": distribution,
            "recent_comments": recent_comments,
        }

    # ── Export (TPS — Report Export) ─────────────────────────────────────

    def build_export_dataset(
        self,
        city_id: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
        status: str = None,
        priority: str = None,
    ) -> dict:
        """Assemble the full report dataset shared by all export formats.

        Mirrors exactly what the Reports screen displays, so PDF/Excel/CSV
        exports always reflect the same filtered data as the UI.
        """
        summary = self.get_complaint_summary(city_id, date_from, date_to, status, priority)
        by_status = self.get_complaints_by_status(city_id, date_from, date_to)["breakdown"]
        by_category = self.get_complaints_by_category(city_id, date_from, date_to, status, priority)["breakdown"]
        by_priority = self.get_complaints_by_priority(city_id, date_from, date_to, status, priority)["breakdown"]
        by_location = self.get_complaints_by_location(city_id, date_from, date_to, status, priority)["breakdown"]
        workers = self.get_worker_performance(city_id, date_from, date_to)["workers"]
        feedback = self.get_citizen_feedback_summary(city_id, date_from, date_to)

        filters_applied = {
            "date_from": date_from.strftime("%Y-%m-%d") if date_from else None,
            "date_to": date_to.strftime("%Y-%m-%d") if date_to else None,
            "status": status,
            "priority": priority,
        }

        return {
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "filters": filters_applied,
            "summary": summary,
            "by_status": by_status,
            "by_category": by_category,
            "by_priority": by_priority,
            "by_location": by_location,
            "workers": workers,
            "feedback": feedback,
        }

    def export_csv(self, dataset: dict) -> str:
        """Render the report dataset as CSV text (RFC 4180 style)."""
        import csv
        import io

        buffer = io.StringIO()
        writer = csv.writer(buffer)

        writer.writerow(["Civic Services Platform - Complaint Report"])
        writer.writerow(["Generated", dataset["generated_at"]])
        filters = dataset["filters"]
        if filters.get("date_from") or filters.get("date_to"):
            writer.writerow([
                "Date range",
                f"{filters.get('date_from') or 'any'} to {filters.get('date_to') or 'any'}",
            ])
        if filters.get("status"):
            writer.writerow(["Status filter", filters["status"]])
        if filters.get("priority"):
            writer.writerow(["Priority filter", filters["priority"]])
        writer.writerow([])

        summary = dataset["summary"]
        writer.writerow(["Summary"])
        writer.writerow(["Total Complaints", summary.get("total", 0)])
        writer.writerow(["Open", summary.get("open", 0)])
        writer.writerow(["Resolved", summary.get("resolved", 0)])
        writer.writerow(["Resolution Rate (%)", summary.get("resolution_rate", 0)])
        writer.writerow(["Avg. Resolution (hrs)", summary.get("avg_resolution_hours") or ""])
        writer.writerow([])

        writer.writerow(["Complaints by Status"])
        writer.writerow(["Status", "Count", "Percentage"])
        for row in dataset["by_status"]:
            writer.writerow([row["status"], row["count"], row["percentage"]])
        writer.writerow([])

        writer.writerow(["Complaints by Category"])
        writer.writerow(["Category", "Count", "Percentage"])
        for row in dataset["by_category"]:
            writer.writerow([row["category"], row["count"], row["percentage"]])
        writer.writerow([])

        writer.writerow(["Complaints by Priority"])
        writer.writerow(["Priority", "Count", "Percentage"])
        for row in dataset["by_priority"]:
            writer.writerow([row["priority"], row["count"], row["percentage"]])
        writer.writerow([])

        writer.writerow(["Complaints by Location"])
        writer.writerow(["City", "Count", "Percentage"])
        for row in dataset["by_location"]:
            writer.writerow([row["city_name"], row["count"], row["percentage"]])
        writer.writerow([])

        writer.writerow(["Field Worker Performance"])
        writer.writerow(
            ["Worker", "Total Assignments", "Completed", "Completion Rate (%)", "Avg. Time (hrs)", "Active"]
        )
        for w in dataset["workers"]:
            writer.writerow([
                w["name"],
                w["total_assignments"],
                w["by_status"].get("completed", 0),
                w["completion_rate"],
                w["avg_completion_hours"] if w["avg_completion_hours"] is not None else "",
                "Yes" if w["is_active"] else "No",
            ])
        writer.writerow([])

        feedback = dataset.get("feedback", {})
        writer.writerow(["Citizen Feedback Summary"])
        writer.writerow(["Total Feedback", feedback.get("total", 0)])
        writer.writerow(["Average Rating", feedback.get("avg_rating") or ""])
        writer.writerow(["Rating", "Count"])
        for star, count in sorted(feedback.get("distribution", {}).items()):
            writer.writerow([f"{star} Star", count])

        return buffer.getvalue()

    def export_excel(self, dataset: dict):
        """Render the report dataset as an in-memory .xlsx workbook (bytes)."""
        import io
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill

        wb = Workbook()
        header_fill = PatternFill(start_color="1D4ED8", end_color="1D4ED8", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        title_font = Font(bold=True, size=14)

        def style_header_row(ws, row_idx, col_count):
            for col in range(1, col_count + 1):
                cell = ws.cell(row=row_idx, column=col)
                cell.font = header_font
                cell.fill = header_fill

        def autosize(ws):
            for column_cells in ws.columns:
                length = max((len(str(cell.value)) if cell.value is not None else 0) for cell in column_cells)
                ws.column_dimensions[column_cells[0].column_letter].width = min(max(length + 2, 10), 40)

        # ── Summary sheet ────────────────────────────────────────────────
        ws = wb.active
        ws.title = "Summary"
        ws.append(["Civic Services Platform - Complaint Report"])
        ws["A1"].font = title_font
        ws.append(["Generated", dataset["generated_at"]])
        filters = dataset["filters"]
        if filters.get("date_from") or filters.get("date_to"):
            ws.append(["Date range", f"{filters.get('date_from') or 'any'} to {filters.get('date_to') or 'any'}"])
        if filters.get("status"):
            ws.append(["Status filter", filters["status"]])
        if filters.get("priority"):
            ws.append(["Priority filter", filters["priority"]])
        ws.append([])

        summary = dataset["summary"]
        ws.append(["Metric", "Value"])
        style_header_row(ws, ws.max_row, 2)
        ws.append(["Total Complaints", summary.get("total", 0)])
        ws.append(["Open", summary.get("open", 0)])
        ws.append(["Resolved", summary.get("resolved", 0)])
        ws.append(["Resolution Rate (%)", summary.get("resolution_rate", 0)])
        ws.append(["Avg. Resolution (hrs)", summary.get("avg_resolution_hours") or ""])
        autosize(ws)

        # ── By status sheet ──────────────────────────────────────────────
        ws2 = wb.create_sheet("By Status")
        ws2.append(["Status", "Count", "Percentage"])
        style_header_row(ws2, 1, 3)
        for row in dataset["by_status"]:
            ws2.append([row["status"], row["count"], row["percentage"]])
        autosize(ws2)

        # ── By category sheet ────────────────────────────────────────────
        ws3 = wb.create_sheet("By Category")
        ws3.append(["Category", "Count", "Percentage"])
        style_header_row(ws3, 1, 3)
        for row in dataset["by_category"]:
            ws3.append([row["category"], row["count"], row["percentage"]])
        autosize(ws3)

        # ── By priority sheet ────────────────────────────────────────────
        ws4 = wb.create_sheet("By Priority")
        ws4.append(["Priority", "Count", "Percentage"])
        style_header_row(ws4, 1, 3)
        for row in dataset["by_priority"]:
            ws4.append([row["priority"], row["count"], row["percentage"]])
        autosize(ws4)

        # ── By location sheet ────────────────────────────────────────────
        ws5 = wb.create_sheet("By Location")
        ws5.append(["City", "Count", "Percentage"])
        style_header_row(ws5, 1, 3)
        for row in dataset["by_location"]:
            ws5.append([row["city_name"], row["count"], row["percentage"]])
        autosize(ws5)

        # ── Worker performance sheet ─────────────────────────────────────
        ws6 = wb.create_sheet("Worker Performance")
        ws6.append(["Worker", "Total Assignments", "Completed", "Completion Rate (%)", "Avg. Time (hrs)", "Active"])
        style_header_row(ws6, 1, 6)
        for w in dataset["workers"]:
            ws6.append([
                w["name"],
                w["total_assignments"],
                w["by_status"].get("completed", 0),
                w["completion_rate"],
                w["avg_completion_hours"] if w["avg_completion_hours"] is not None else "",
                "Yes" if w["is_active"] else "No",
            ])
        autosize(ws6)

        # ── Feedback sheet ────────────────────────────────────────────────
        ws7 = wb.create_sheet("Citizen Feedback")
        feedback = dataset.get("feedback", {})
        ws7.append(["Citizen Feedback Summary"])
        ws7["A1"].font = title_font
        ws7.append([])
        ws7.append(["Metric", "Value"])
        style_header_row(ws7, ws7.max_row, 2)
        ws7.append(["Total Feedback", feedback.get("total", 0)])
        ws7.append(["Average Rating", feedback.get("avg_rating") or ""])
        ws7.append([])
        ws7.append(["Rating", "Count"])
        style_header_row(ws7, ws7.max_row, 2)
        for star, count in sorted(feedback.get("distribution", {}).items()):
            ws7.append([f"{star} Star", count])
        autosize(ws7)

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def export_pdf(self, dataset: dict) -> bytes:
        """Render the report dataset as a paginated PDF document (bytes)."""
        import io
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        )
        styles = getSampleStyleSheet()
        story = [
            Paragraph("Civic Services Platform &mdash; Complaint Report", styles["Title"]),
            Paragraph(f"Generated: {dataset['generated_at']}", styles["Normal"]),
        ]

        filters = dataset["filters"]
        if filters.get("date_from") or filters.get("date_to"):
            story.append(Paragraph(
                f"Date range: {filters.get('date_from') or 'any'} to {filters.get('date_to') or 'any'}",
                styles["Normal"],
            ))
        if filters.get("status"):
            story.append(Paragraph(f"Status filter: {filters['status']}", styles["Normal"]))
        if filters.get("priority"):
            story.append(Paragraph(f"Priority filter: {filters['priority']}", styles["Normal"]))
        story.append(Spacer(1, 0.5 * cm))

        table_style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D4ED8")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])

        def add_section(title, header, rows):
            story.append(Paragraph(title, styles["Heading2"]))
            if not rows:
                story.append(Paragraph("No data.", styles["Normal"]))
            else:
                table_data = [header] + rows
                table = Table(table_data, hAlign="LEFT", repeatRows=1)
                table.setStyle(table_style)
                story.append(table)
            story.append(Spacer(1, 0.4 * cm))

        summary = dataset["summary"]
        add_section("Summary", ["Metric", "Value"], [
            ["Total Complaints", str(summary.get("total", 0))],
            ["Open", str(summary.get("open", 0))],
            ["Resolved", str(summary.get("resolved", 0))],
            ["Resolution Rate (%)", str(summary.get("resolution_rate", 0))],
            ["Avg. Resolution (hrs)", str(summary.get("avg_resolution_hours") or "-")],
        ])

        add_section("Complaints by Status", ["Status", "Count", "Percentage"], [
            [r["status"], str(r["count"]), f"{r['percentage']}%"] for r in dataset["by_status"]
        ])

        add_section("Complaints by Category", ["Category", "Count", "Percentage"], [
            [r["category"], str(r["count"]), f"{r['percentage']}%"] for r in dataset["by_category"]
        ])

        add_section("Complaints by Priority", ["Priority", "Count", "Percentage"], [
            [r["priority"], str(r["count"]), f"{r['percentage']}%"] for r in dataset["by_priority"]
        ])

        add_section("Complaints by Location", ["City", "Count", "Percentage"], [
            [r["city_name"], str(r["count"]), f"{r['percentage']}%"] for r in dataset["by_location"]
        ])

        add_section(
            "Field Worker Performance",
            ["Worker", "Total", "Completed", "Rate (%)", "Avg (hrs)", "Active"],
            [
                [
                    w["name"],
                    str(w["total_assignments"]),
                    str(w["by_status"].get("completed", 0)),
                    f"{w['completion_rate']}%",
                    str(w["avg_completion_hours"]) if w["avg_completion_hours"] is not None else "-",
                    "Yes" if w["is_active"] else "No",
                ]
                for w in dataset["workers"]
            ],
        )

        # ── Citizen feedback section ─────────────────────────────────────
        feedback = dataset.get("feedback", {})
        add_section("Citizen Feedback Summary", ["Metric", "Value"], [
            ["Total Feedback", str(feedback.get("total", 0))],
            ["Average Rating", str(feedback.get("avg_rating") or "-")],
        ])
        dist = feedback.get("distribution", {})
        if dist:
            add_section("Rating Distribution", ["Rating", "Count"], [
                [f"{star} Star", str(count)] for star, count in sorted(dist.items())
            ])

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
