"""
Unit tests for Marshmallow schemas.
"""

import pytest
from marshmallow import ValidationError
from app.schemas.user_schema import UserCreateSchema, MunicipalAdminCreateSchema
from app.schemas.complaint_schema import ComplaintCreateSchema
from app.schemas.feedback_schema import FeedbackCreateSchema
from app.schemas.verification_schema import VerificationDecisionSchema


class TestUserCreateSchema:
    """Unit tests for UserCreateSchema."""

    def test_valid_data_passes(self):
        schema = UserCreateSchema()
        data = {
            "username": "citizen1",
            "email": "citizen@example.com",
            "password": "Password123!",
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
            "image_url": "/api/v1/citizen/complaints/media/photo.jpg",
        }
        result = schema.load(data)
        assert result["category"] == "pothole"
        # Priority is intentionally left out when not provided — the service
        # layer applies the configured `default_complaint_priority` system
        # setting (TPS-99), not a hardcoded schema default.
        assert "priority" not in result

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


class TestVerificationDecisionSchema:
    def test_valid_decisions_pass(self):
        schema = VerificationDecisionSchema()
        result = schema.load({
            "decision": "rework_requested",
            "remarks": "Repair the unfinished edge.",
        })
        assert result["decision"] == "rework_requested"

    def test_invalid_decision_raises(self):
        with pytest.raises(ValidationError):
            VerificationDecisionSchema().load({"decision": "rejected"})


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
            "pincode": "226001",
        })
        assert result["pincode"] == "226001"
        assert result["email"] == "municipal@example.com"

    def test_pincode_required(self):
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
                "pincode": "226001",
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
                "pincode": "226001",
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
                "pincode": "226001",
            })
        assert "phone" in exc.value.messages

    def test_invalid_pincode_is_rejected(self):
        schema = MunicipalAdminCreateSchema()
        with pytest.raises(ValidationError) as exc:
            schema.load({
                "username": "municipal1",
                "email": "municipal@example.com",
                "password": "Password123!",
                "confirm_password": "Password123!",
                "first_name": "Municipal",
                "last_name": "Admin",
                "pincode": "22",
            })
        assert "pincode" in exc.value.messages
