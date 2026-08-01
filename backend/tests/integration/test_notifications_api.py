"""
Integration tests for TPS-91: View Notifications.
"""

from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.notification import Notification


class TestNotificationsEndpoints:
    """Integration tests for the /api/v1/notifications endpoints."""

    @staticmethod
    def _register_and_login(client, email: str):
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "username": email.split("@")[0],
                "email": email,
                "password": "Password123!",
                "first_name": "Notif",
                "last_name": "Tester",
                "pincode": "226001",
            },
        )
        assert register_response.status_code == 201

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Password123!"},
        )
        assert login_response.status_code == 200
        return login_response.get_json()["data"]

    @staticmethod
    def _create_notification(app, user_id: int, title: str, is_read: bool = False, created_at=None):
        with app.app_context():
            notification = Notification(
                user_id=user_id,
                title=title,
                message=f"Message for {title}",
                notification_type=Notification.TYPE_GENERAL,
                is_read=is_read,
            )
            if created_at is not None:
                notification.created_at = created_at
            db.session.add(notification)
            db.session.commit()
            return notification.id

    def test_user_can_list_own_notifications(self, app, client):
        """AC 1, 6: authenticated user can access the Notification Center and it loads."""
        auth_data = self._register_and_login(client, "notif-list@example.com")
        user_id = auth_data["user"]["id"]
        self._create_notification(app, user_id, "First notification")
        self._create_notification(app, user_id, "Second notification")

        response = client.get(
            "/api/v1/notifications/",
            headers={"Authorization": f"Bearer {auth_data['access_token']}"},
        )
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        assert payload["data"]["pagination"]["total"] == 2
        assert len(payload["data"]["items"]) == 2

    def test_notifications_are_returned_in_chronological_order(self, app, client):
        """AC 2: newest notification first."""
        auth_data = self._register_and_login(client, "notif-order@example.com")
        user_id = auth_data["user"]["id"]
        now = datetime.now(timezone.utc)
        self._create_notification(app, user_id, "Oldest", created_at=now - timedelta(minutes=5))
        self._create_notification(app, user_id, "Newest", created_at=now)

        response = client.get(
            "/api/v1/notifications/",
            headers={"Authorization": f"Bearer {auth_data['access_token']}"},
        )
        titles = [item["title"] for item in response.get_json()["data"]["items"]]

        assert titles == ["Newest", "Oldest"]

    def test_read_and_unread_notifications_are_distinguished(self, app, client):
        """AC 3: is_read flag is present and correct per notification."""
        auth_data = self._register_and_login(client, "notif-readflag@example.com")
        user_id = auth_data["user"]["id"]
        self._create_notification(app, user_id, "Unread one", is_read=False)
        self._create_notification(app, user_id, "Already read", is_read=True)

        response = client.get(
            "/api/v1/notifications/",
            headers={"Authorization": f"Bearer {auth_data['access_token']}"},
        )
        items = {item["title"]: item["is_read"] for item in response.get_json()["data"]["items"]}

        assert items["Unread one"] is False
        assert items["Already read"] is True

    def test_unread_only_filter(self, app, client):
        """AC 3: unread_only query param filters out read notifications."""
        auth_data = self._register_and_login(client, "notif-unreadfilter@example.com")
        user_id = auth_data["user"]["id"]
        self._create_notification(app, user_id, "Unread one", is_read=False)
        self._create_notification(app, user_id, "Already read", is_read=True)

        response = client.get(
            "/api/v1/notifications/",
            headers={"Authorization": f"Bearer {auth_data['access_token']}"},
            query_string={"unread_only": "true"},
        )
        items = response.get_json()["data"]["items"]

        assert len(items) == 1
        assert items[0]["title"] == "Unread one"

    def test_user_can_view_a_single_notification(self, app, client):
        """AC 5: notification details can be viewed."""
        auth_data = self._register_and_login(client, "notif-detail@example.com")
        user_id = auth_data["user"]["id"]
        notif_id = self._create_notification(app, user_id, "Detail view")

        response = client.get(
            f"/api/v1/notifications/{notif_id}",
            headers={"Authorization": f"Bearer {auth_data['access_token']}"},
        )
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["data"]["notification"]["title"] == "Detail view"

    def test_user_can_mark_a_single_notification_as_read(self, app, client):
        """AC 4: user can mark notifications as read."""
        auth_data = self._register_and_login(client, "notif-markread@example.com")
        user_id = auth_data["user"]["id"]
        notif_id = self._create_notification(app, user_id, "Mark me", is_read=False)

        response = client.patch(
            f"/api/v1/notifications/{notif_id}/read",
            headers={"Authorization": f"Bearer {auth_data['access_token']}"},
        )
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["data"]["notification"]["is_read"] is True
        assert payload["data"]["notification"]["read_at"] is not None

    def test_marking_already_read_notification_is_idempotent(self, app, client):
        """Mark-as-read on an already-read notification succeeds without error."""
        auth_data = self._register_and_login(client, "notif-idempotent@example.com")
        user_id = auth_data["user"]["id"]
        notif_id = self._create_notification(app, user_id, "Already read", is_read=True)

        response = client.patch(
            f"/api/v1/notifications/{notif_id}/read",
            headers={"Authorization": f"Bearer {auth_data['access_token']}"},
        )
        assert response.status_code == 200
        assert response.get_json()["data"]["notification"]["is_read"] is True

    def test_user_can_mark_all_notifications_as_read(self, app, client):
        """AC 4: mark-all-as-read clears every unread notification for the user."""
        auth_data = self._register_and_login(client, "notif-markall@example.com")
        user_id = auth_data["user"]["id"]
        self._create_notification(app, user_id, "One", is_read=False)
        self._create_notification(app, user_id, "Two", is_read=False)

        response = client.patch(
            "/api/v1/notifications/read-all",
            headers={"Authorization": f"Bearer {auth_data['access_token']}"},
        )
        assert response.status_code == 200
        assert response.get_json()["data"]["marked_read"] == 2

        listing = client.get(
            "/api/v1/notifications/",
            headers={"Authorization": f"Bearer {auth_data['access_token']}"},
        )
        assert all(item["is_read"] for item in listing.get_json()["data"]["items"])

    def test_unread_count_reflects_unread_notifications(self, app, client):
        """Supports the header badge: unread count matches actual unread notifications."""
        auth_data = self._register_and_login(client, "notif-count@example.com")
        user_id = auth_data["user"]["id"]
        self._create_notification(app, user_id, "Unread A", is_read=False)
        self._create_notification(app, user_id, "Unread B", is_read=False)
        self._create_notification(app, user_id, "Read one", is_read=True)

        response = client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {auth_data['access_token']}"},
        )
        assert response.get_json()["data"]["count"] == 2

    def test_user_cannot_view_another_users_notification(self, app, client):
        """Ownership check: notifications are private to the recipient."""
        owner_auth = self._register_and_login(client, "notif-owner@example.com")
        owner_id = owner_auth["user"]["id"]
        notif_id = self._create_notification(app, owner_id, "Private notification")

        intruder_auth = self._register_and_login(client, "notif-intruder@example.com")
        response = client.get(
            f"/api/v1/notifications/{notif_id}",
            headers={"Authorization": f"Bearer {intruder_auth['access_token']}"},
        )
        assert response.status_code == 404

    def test_user_cannot_mark_another_users_notification_as_read(self, app, client):
        """Ownership check applies to the mark-as-read endpoint too."""
        owner_auth = self._register_and_login(client, "notif-owner2@example.com")
        owner_id = owner_auth["user"]["id"]
        notif_id = self._create_notification(app, owner_id, "Private notification")

        intruder_auth = self._register_and_login(client, "notif-intruder2@example.com")
        response = client.patch(
            f"/api/v1/notifications/{notif_id}/read",
            headers={"Authorization": f"Bearer {intruder_auth['access_token']}"},
        )
        assert response.status_code == 404

    def test_notifications_endpoint_requires_authentication(self, client):
        """Unauthenticated requests are rejected."""
        response = client.get("/api/v1/notifications/")
        assert response.status_code == 401
