"""
Reports service — analytics and statistics for the administrator dashboard.

All queries run directly on the database using SQLAlchemy aggregations.
SQLite-compatible: date grouping uses strftime().
"""

from sqlalchemy import func

from app.extensions import db
from app.models.complaint import Complaint
from app.models.complaint_assignment import ComplaintAssignment
from app.models.role import Role
from app.models.user import User


class ReportsService:
    """Generates statistical reports for administrators."""

    # ── Summary ───────────────────────────────────────────────────────────

    def get_complaint_summary(self) -> dict:
        """Overall complaint statistics: totals, resolution rate, avg time."""
        total = Complaint.query.count()

        by_status = {
            s: Complaint.query.filter_by(status=s).count()
            for s in Complaint.VALID_STATUSES
        }

        by_category = {}
        for row in (
            db.session.query(
                Complaint.category, func.count(Complaint.id)
            ).group_by(Complaint.category).all()
        ):
            by_category[row[0]] = row[1]

        # Complaints with a resolved_at timestamp
        resolved_count = Complaint.query.filter(
            Complaint.resolved_at.isnot(None)
        ).count()

        # Average resolution time in hours (SQLite: julianday diff * 24)
        avg_hours = None
        if resolved_count:
            result = db.session.query(
                func.avg(
                    (func.julianday(Complaint.resolved_at) -
                     func.julianday(Complaint.created_at)) * 24
                )
            ).filter(Complaint.resolved_at.isnot(None)).scalar()
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
        }

    # ── By status ─────────────────────────────────────────────────────────

    def get_complaints_by_status(self) -> dict:
        """Counts and percentages for each complaint status."""
        total = Complaint.query.count()
        rows = (
            db.session.query(Complaint.status, func.count(Complaint.id))
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

    def get_complaints_by_category(self) -> dict:
        """Counts and percentages per complaint category."""
        total = Complaint.query.count()
        rows = (
            db.session.query(Complaint.category, func.count(Complaint.id))
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

    # ── Trends ────────────────────────────────────────────────────────────

    def get_complaint_trends(self, period: str = "daily") -> dict:
        """Complaint submission counts grouped by time period.

        Args:
            period: One of ``daily`` (last 30 days), ``weekly`` (last 12 weeks),
                    ``monthly`` (last 12 months).

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

        rows = (
            db.session.query(
                func.strftime(fmt, Complaint.created_at).label("period"),
                func.count(Complaint.id).label("count"),
            )
            .group_by("period")
            .order_by("period")
            .all()
        )

        # Limit to recent windows
        limit = {"daily": 30, "weekly": 12, "monthly": 12}[period]
        trend_data = [{"period": r.period, "count": r.count} for r in rows]
        trend_data = trend_data[-limit:]

        return {"period": period, "data": trend_data}

    # ── Worker performance ────────────────────────────────────────────────

    def get_worker_performance(self) -> dict:
        """Per-field-worker assignment statistics."""
        fw_role = Role.query.filter_by(name=Role.FIELD_WORKER).first()
        if not fw_role:
            return {"workers": []}

        workers = User.query.filter_by(role_id=fw_role.id).all()
        results = []

        for worker in workers:
            base = ComplaintAssignment.query.filter_by(worker_id=worker.id)
            total = base.count()

            by_status = {
                s: base.filter_by(status=s).count()
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
                result = db.session.query(
                    func.avg(
                        (func.julianday(ComplaintAssignment.completed_at) -
                         func.julianday(ComplaintAssignment.accepted_at)) * 24
                    )
                ).filter(
                    ComplaintAssignment.worker_id == worker.id,
                    ComplaintAssignment.status == ComplaintAssignment.STATUS_COMPLETED,
                    ComplaintAssignment.accepted_at.isnot(None),
                    ComplaintAssignment.completed_at.isnot(None),
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
