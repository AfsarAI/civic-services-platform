"""
Notifications controller — read and manage notifications for any authenticated user.

All endpoints require a valid JWT; no role restriction (notifications are
sent to citizens, field workers, and administrators alike).
Covered Jira stories: TPS-91, TPS-92, TPS-93, TPS-94
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.notifications.service import NotificationService
from app.utils.responses import success_response, error_response, paginated_response

ns = Namespace(
    "notifications", description="User notifications", path="/notifications"
)
_svc = NotificationService()

# ── Swagger models (docs only) ────────────────────────────────────────────

_envelope = ns.model("NotifEnvelope", {
    "success": fields.Boolean,
    "message": fields.String,
    "data": fields.Raw,
    "errors": fields.Raw,
})


# ── Endpoints ─────────────────────────────────────────────────────────────

@ns.route("/")
class NotificationListResource(Resource):

    @ns.response(200, "Paginated notifications", _envelope)
    @ns.response(401, "Unauthorised")
    @jwt_required()
    def get(self):
        """List notifications for the authenticated user (TPS-91).

        Query params: page, per_page, unread_only (true/false).
        """
        user_id = int(get_jwt_identity())
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        unread_only = request.args.get("unread_only", "").lower() == "true"

        result = _svc.get_user_notifications(user_id, page, per_page, unread_only)
        return paginated_response(
            result["items"], result["total"],
            result["page"], result["per_page"],
            "Notifications retrieved.",
        )


@ns.route("/<int:notification_id>")
@ns.param("notification_id", "Notification ID")
class NotificationResource(Resource):

    @ns.response(200, "Notification details", _envelope)
    @ns.response(404, "Not found", _envelope)
    @jwt_required()
    def get(self, notification_id):
        """Get a specific notification (TPS-92)."""
        user_id = int(get_jwt_identity())
        try:
            data = _svc.get_notification(notification_id, user_id)
            return success_response(data, "Notification retrieved.")
        except ValueError as exc:
            return error_response(str(exc), status_code=404)


@ns.route("/<int:notification_id>/read")
@ns.param("notification_id", "Notification ID")
class NotificationReadResource(Resource):

    @ns.response(200, "Notification marked as read", _envelope)
    @ns.response(404, "Not found", _envelope)
    @jwt_required()
    def patch(self, notification_id):
        """Mark a single notification as read (TPS-93)."""
        user_id = int(get_jwt_identity())
        try:
            data = _svc.mark_as_read(notification_id, user_id)
            return success_response(data, "Notification marked as read.")
        except ValueError as exc:
            return error_response(str(exc), status_code=404)


@ns.route("/read-all")
class NotificationReadAllResource(Resource):

    @ns.response(200, "All notifications marked as read", _envelope)
    @ns.response(401, "Unauthorised")
    @jwt_required()
    def patch(self):
        """Mark all notifications as read for the authenticated user (TPS-94)."""
        user_id = int(get_jwt_identity())
        data = _svc.mark_all_as_read(user_id)
        return success_response(data, "All notifications marked as read.")


@ns.route("/unread-count")
class NotificationUnreadCountResource(Resource):

    @ns.response(200, "Unread count", _envelope)
    @ns.response(401, "Unauthorised")
    @jwt_required()
    def get(self):
        """Get the number of unread notifications for the authenticated user."""
        user_id = int(get_jwt_identity())
        data = _svc.get_unread_count(user_id)
        return success_response(data, "Unread count retrieved.")
