"""
Unit tests for NotificationService — isolated from HTTP plumbing, calling
the service layer directly against the real (in-memory) database.
"""

import pytest
from app.api.notifications.service import NotificationService
from app.extensions import db
from app.models.notification import Notification
from app.models.role import Role
from app.models.user import User


def _make_user(email: str) -> User:
    role = Role.query.filter_by(name=Role.CITIZEN).first()
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(
        username=email.split("@")[0],
        email=email,
        first_name="Test",
        last_name="User",
        role_id=role.id,
        is_active=True,
    )
    user.set_password("Citizen@123")
    db.session.add(user)
    db.session.commit()
    return user


class TestNotificationServiceSendAndSerialize:
    """Unit tests for send_notification."""

    def test_send_notification_persists_and_returns_dict(self, app):
        with app.app_context():
            user = _make_user("unit.notif.send1@example.com")
            service = NotificationService()
            result = service.send_notification(
                user_id=user.id,
                title="Test title",
                message="Test message body",
                related_complaint_id=None,
            )
            assert result["title"] == "Test title"
            assert result["is_read"] is False
            assert Notification.query.get(result["id"]) is not None

    def test_send_notification_with_commit_false_only_flushes(self, app):
        with app.app_context():
            user = _make_user("unit.notif.send2@example.com")
            service = NotificationService()
            result = service.send_notification(
                user_id=user.id,
                title="Flushed only",
                message="Not committed yet",
                commit=False,
            )
            # Still visible within the same open transaction via flush.
            assert Notification.query.get(result["id"]) is not None
            db.session.commit()


class TestNotificationServiceListAndGet:
    """Unit tests for get_user_notifications, get_notification, get_unread_count."""

    def test_get_user_notifications_returns_own_only(self, app):
        with app.app_context():
            user = _make_user("unit.notif.list1@example.com")
            other = _make_user("unit.notif.list2@example.com")
            service = NotificationService()
            service.send_notification(user.id, "Mine", "Mine body")
            service.send_notification(other.id, "Not mine", "Not mine body")
            result = service.get_user_notifications(user.id)
            assert all(item["user_id"] == user.id for item in result["items"])

    def test_get_user_notifications_unread_only_filter(self, app):
        with app.app_context():
            user = _make_user("unit.notif.list3@example.com")
            service = NotificationService()
            n1 = service.send_notification(user.id, "Unread", "Body")
            n2 = service.send_notification(user.id, "Will be read", "Body")
            service.mark_as_read(n2["id"], user.id)
            result = service.get_user_notifications(user.id, unread_only=True)
            ids = [item["id"] for item in result["items"]]
            assert n1["id"] in ids
            assert n2["id"] not in ids

    def test_get_notification_returns_owned_notification(self, app):
        with app.app_context():
            user = _make_user("unit.notif.get1@example.com")
            service = NotificationService()
            created = service.send_notification(user.id, "Title", "Body")
            result = service.get_notification(created["id"], user.id)
            assert result["notification"]["id"] == created["id"]

    def test_get_notification_rejects_other_users_notification(self, app):
        with app.app_context():
            owner = _make_user("unit.notif.get2@example.com")
            other = _make_user("unit.notif.get3@example.com")
            service = NotificationService()
            created = service.send_notification(owner.id, "Title", "Body")
            with pytest.raises(ValueError, match="permission"):
                service.get_notification(created["id"], other.id)

    def test_get_notification_rejects_missing_notification(self, app):
        with app.app_context():
            user = _make_user("unit.notif.get4@example.com")
            service = NotificationService()
            with pytest.raises(ValueError, match="not found"):
                service.get_notification(999999, user.id)

    def test_get_unread_count_reflects_unread_notifications(self, app):
        with app.app_context():
            user = _make_user("unit.notif.count1@example.com")
            service = NotificationService()
            service.send_notification(user.id, "One", "Body")
            service.send_notification(user.id, "Two", "Body")
            result = service.get_unread_count(user.id)
            assert result["count"] >= 2


class TestNotificationServiceMarkAsRead:
    """Unit tests for mark_as_read and mark_all_as_read."""

    def test_mark_as_read_sets_is_read_and_read_at(self, app):
        with app.app_context():
            user = _make_user("unit.notif.mark1@example.com")
            service = NotificationService()
            created = service.send_notification(user.id, "Title", "Body")
            result = service.mark_as_read(created["id"], user.id)
            assert result["notification"]["is_read"] is True
            assert result["notification"]["read_at"] is not None

    def test_mark_as_read_is_idempotent(self, app):
        with app.app_context():
            user = _make_user("unit.notif.mark2@example.com")
            service = NotificationService()
            created = service.send_notification(user.id, "Title", "Body")
            service.mark_as_read(created["id"], user.id)
            first_read_at = Notification.query.get(created["id"]).read_at
            service.mark_as_read(created["id"], user.id)
            assert Notification.query.get(created["id"]).read_at == first_read_at

    def test_mark_as_read_rejects_other_users_notification(self, app):
        with app.app_context():
            owner = _make_user("unit.notif.mark3@example.com")
            other = _make_user("unit.notif.mark4@example.com")
            service = NotificationService()
            created = service.send_notification(owner.id, "Title", "Body")
            with pytest.raises(ValueError, match="permission"):
                service.mark_as_read(created["id"], other.id)

    def test_mark_all_as_read_updates_only_unread_notifications(self, app):
        with app.app_context():
            user = _make_user("unit.notif.markall1@example.com")
            service = NotificationService()
            service.send_notification(user.id, "One", "Body")
            service.send_notification(user.id, "Two", "Body")
            result = service.mark_all_as_read(user.id)
            assert result["marked_read"] >= 2
            assert service.get_unread_count(user.id)["count"] == 0
