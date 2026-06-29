"""
Notifications controller — user notification endpoints.
"""

from flask_restx import Namespace, Resource

ns = Namespace("notifications", description="User notifications", path="/notifications")


@ns.route("/")
class NotificationListResource(Resource):
    @ns.response(200, "List of notifications")
    @ns.response(401, "Unauthorised")
    def get(self):
        """Get all notifications for the current user."""
        # TODO: implement via NotificationService
        return {"success": True, "message": "Not yet implemented", "data": []}, 501


@ns.route("/<int:notification_id>")
@ns.param("notification_id", "The notification identifier")
class NotificationResource(Resource):
    @ns.response(200, "Notification details")
    @ns.response(404, "Not found")
    def get(self, notification_id: int):
        """Get a specific notification."""
        # TODO: implement via NotificationService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501


@ns.route("/<int:notification_id>/read")
@ns.param("notification_id", "The notification identifier")
class NotificationReadResource(Resource):
    @ns.response(200, "Notification marked as read")
    def patch(self, notification_id: int):
        """Mark a notification as read."""
        # TODO: implement via NotificationService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501


@ns.route("/read-all")
class NotificationReadAllResource(Resource):
    @ns.response(200, "All notifications marked as read")
    def patch(self):
        """Mark all notifications as read."""
        # TODO: implement via NotificationService
        return {"success": True, "message": "Not yet implemented", "data": None}, 501


@ns.route("/unread-count")
class NotificationUnreadCountResource(Resource):
    @ns.response(200, "Unread notification count")
    def get(self):
        """Get the count of unread notifications."""
        # TODO: implement via NotificationService
        return {"success": True, "message": "Not yet implemented", "data": {"count": 0}}, 501
