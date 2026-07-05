"""
Unit tests for Marshmallow schemas.
"""

import pytest
from marshmallow import ValidationError
from app.schemas.user_schema import UserCreateSchema, MunicipalAdminCreateSchema
from app.schemas.complaint_schema import ComplaintCreateSchema
from app.schemas.feedback_schema import FeedbackCreateSchema


class TestUserCreateSchema:
    """Unit tests for UserCreateSchema."""

    def test_valid_data_passes(self):
        schema = UserCreateSchema()
        data = {
            "username": "citizen1",
            "email": "citizen@example.com",
            "password": "Password123",
            "first_name": "Alice",
            "last_name": "Smith",
            "role_id": 1,
        }
        result = schema.load(data)
        assert result["username"] == "citizen1"

    def test_invalid_email_raises(self):
        schema = UserCreateSchema()
        with pytest.raises(ValidationError):
            schema.load({"username": "u", "email": "not-an-email", "password": "pass", "first_name": "A", "last_name": "B", "role_id": 1})

    def test_short_password_raises(self):
        schema = UserCreateSchema()
        with pytest.raises(ValidationError):
            schema.load({"username": "user1", "email": "a@b.com", "password": "short", "first_name": "A", "last_name": "B", "role_id": 1})


class TestComplaintCreateSchema:
    """Unit tests for ComplaintCreateSchema."""

    def test_valid_complaint_passes(self):
        schema = ComplaintCreateSchema()
        data = {
            "title": "Large pothole on Main Street",
            "description": "There is a large pothole causing accidents.",
            "category": "pothole",
        }
        result = schema.load(data)
        assert result["category"] == "pothole"
        assert result["priority"] == "medium"

    def test_invalid_category_raises(self):
        schema = ComplaintCreateSchema()
        with pytest.raises(ValidationError):
            schema.load({"title": "Test", "description": "A long enough description.", "category": "invalid_category"})


class TestFeedbackCreateSchema:
    """Unit tests for FeedbackCreateSchema."""

    def test_rating_out_of_range_raises(self):
        schema = FeedbackCreateSchema()
        with pytest.raises(ValidationError):
            schema.load({"rating": 6})

    def test_valid_feedback_passes(self):
        schema = FeedbackCreateSchema()
        result = schema.load({"rating": 5, "comment": "Great service!"})
        assert result["rating"] == 5


class TestMunicipalAdminCreateSchema:
    """Unit tests for MunicipalAdminCreateSchema."""

    def test_valid_data_passes(self):
        schema = MunicipalAdminCreateSchema()
        result = schema.load({
            "username": "municipal1",
            "email": "municipal@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "first_name": "Municipal",
            "last_name": "Admin",
            "city_name": "Lucknow",
        })
        assert result["city_name"] == "Lucknow"
        assert result["email"] == "municipal@example.com"

    def test_city_name_required(self):
        schema = MunicipalAdminCreateSchema()
        with pytest.raises(ValidationError):
            schema.load({
                "username": "municipal1",
                "email": "municipal@example.com",
                "password": "Password123!",
                "confirm_password": "Password123!",
                "first_name": "Municipal",
                "last_name": "Admin",
            })

    def test_confirm_password_must_match(self):
        schema = MunicipalAdminCreateSchema()
        with pytest.raises(ValidationError) as exc:
            schema.load({
                "username": "municipal1",
                "email": "municipal@example.com",
                "password": "Password123!",
                "confirm_password": "Password999!",
                "first_name": "Municipal",
                "last_name": "Admin",
                "city_name": "Lucknow",
            })
        assert "confirm_password" in exc.value.messages

    def test_weak_password_is_rejected(self):
        schema = MunicipalAdminCreateSchema()
        with pytest.raises(ValidationError) as exc:
            schema.load({
                "username": "municipal1",
                "email": "municipal@example.com",
                "password": "password123",
                "confirm_password": "password123",
                "first_name": "Municipal",
                "last_name": "Admin",
                "city_name": "Lucknow",
            })
        assert "password" in exc.value.messages

    def test_invalid_phone_is_rejected(self):
        schema = MunicipalAdminCreateSchema()
        with pytest.raises(ValidationError) as exc:
            schema.load({
                "username": "municipal1",
                "email": "municipal@example.com",
                "password": "Password123!",
                "confirm_password": "Password123!",
                "first_name": "Municipal",
                "last_name": "Admin",
                "phone": "not-a-phone",
                "city_name": "Lucknow",
            })
        assert "phone" in exc.value.messages
