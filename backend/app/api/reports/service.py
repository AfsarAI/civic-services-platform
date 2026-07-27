"""
Reports service — analytics and statistics for the administrator dashboard.

All queries run directly on the database using SQLAlchemy aggregations.
SQLite-compatible: date grouping uses strftime().

Every report accepts an optional ``city_id`` (municipal administrators are
scoped to their own city; ``None`` means unscoped, i.e. system administrators)
plus optional ``date_from``/``date_to``/``status`` filters (TPS-85/96/97/98,
AC3/AC4).
"""

from datetime import datetime, timedelta

from sqlalchemy import func

from app.models.city import City
from app.models.complaint import Complaint
from app.models.complaint_assignment import ComplaintAssignment
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

    @staticmethod
    def _filtered_query(
        city_id: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
        status: str = None,
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
        return query

    # ── Summary ───────────────────────────────────────────────────────────

    def get_complaint_summary(
        self,
        city_id: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
        status: str = None,
    ) -> dict:
        """Overall complaint statistics: totals, resolution rate, avg time."""
        base = self._filtered_query(city_id, date_from, date_to, status)
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
    ) -> dict:
        """Counts and percentages per complaint category."""
        base = self._filtered_query(city_id, date_from, date_to, status)
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
    ) -> dict:
        """Counts and percentages per complaint priority."""
        base = self._filtered_query(city_id, date_from, date_to, status)
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
    ) -> dict:
        """Counts and percentages per city.

        For a municipal administrator (``city_id`` provided) this naturally
        collapses to a single row for their own city.
        """
        base = self._filtered_query(city_id, date_from, date_to, status)
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

        base = self._filtered_query(city_id, date_from, date_to, status)
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
