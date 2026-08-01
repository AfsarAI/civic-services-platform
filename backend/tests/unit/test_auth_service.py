"""
Unit tests for AuthService — isolated from HTTP/JWT plumbing, calling the
service layer directly against the real (in-memory) database.
"""

import pytest
from app.api.auth.service import AuthService
from app.extensions import db
from app.models.city import City
from app.models.role import Role
from app.models.user import User
from app.services.system_settings_service import SystemSettingsService


def _make_citizen(email: str, pincode: str = "226001", is_active: bool = True) -> User:
    role = Role.query.filter_by(name=Role.CITIZEN).first()
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(
        username=email.split("@")[0],
        email=email,
        first_name="Test",
        last_name="Citizen",
        role_id=role.id,
        pincode=pincode,
        is_active=is_active,
    )
    user.set_password("Citizen@123")
    db.session.add(user)
    db.session.commit()
    return user


class TestAuthServiceRegisterUser:
    """Unit tests for AuthService.register_user."""

    def test_register_user_creates_citizen_account(self, app):
        with app.app_context():
            service = AuthService()
            result = service.register_user({
                "username": "unit_register_1",
                "email": "unit.register1@example.com",
                "password": "Citizen@123",
                "first_name": "Unit",
                "last_name": "Tester",
                "pincode": "226001",
            })
            assert result["user"]["email"] == "unit.register1@example.com"
            assert result["user"]["role"] == Role.CITIZEN

    def test_register_user_rejects_duplicate_email(self, app):
        with app.app_context():
            service = AuthService()
            payload = {
                "username": "unit_register_2",
                "email": "unit.register2@example.com",
                "password": "Citizen@123",
                "first_name": "Unit",
                "last_name": "Tester",
                "pincode": "226001",
            }
            service.register_user(payload)
            with pytest.raises(ValueError, match="email"):
                service.register_user({**payload, "username": "unit_register_2b"})

    def test_register_user_rejects_duplicate_username(self, app):
        with app.app_context():
            service = AuthService()
            payload = {
                "username": "unit_register_3",
                "email": "unit.register3@example.com",
                "password": "Citizen@123",
                "first_name": "Unit",
                "last_name": "Tester",
                "pincode": "226001",
            }
            service.register_user(payload)
            with pytest.raises(ValueError, match="username"):
                service.register_user({**payload, "email": "unit.register3b@example.com"})

    def test_register_user_rejects_unmapped_pincode(self, app):
        with app.app_context():
            service = AuthService()
            with pytest.raises(ValueError, match="pincode"):
                service.register_user({
                    "username": "unit_register_4",
                    "email": "unit.register4@example.com",
                    "password": "Citizen@123",
                    "first_name": "Unit",
                    "last_name": "Tester",
                    "pincode": "999999",
                })


class TestAuthServiceLogin:
    """Unit tests for AuthService.login."""

    def test_login_with_valid_credentials_returns_tokens(self, app):
        with app.app_context():
            _make_citizen("unit.login1@example.com")
            service = AuthService()
            result = service.login("unit.login1@example.com", "Citizen@123")
            assert "access_token" in result
            assert "refresh_token" in result
            assert result["user"]["email"] == "unit.login1@example.com"

    def test_login_with_wrong_password_raises(self, app):
        with app.app_context():
            _make_citizen("unit.login2@example.com")
            service = AuthService()
            with pytest.raises(ValueError, match="Invalid email or password"):
                service.login("unit.login2@example.com", "WrongPass123")

    def test_login_with_unknown_email_raises(self, app):
        with app.app_context():
            service = AuthService()
            with pytest.raises(ValueError, match="Invalid email or password"):
                service.login("does.not.exist@example.com", "Whatever123")

    def test_login_with_inactive_account_raises(self, app):
        with app.app_context():
            _make_citizen("unit.login3@example.com", is_active=False)
            service = AuthService()
            with pytest.raises(ValueError, match="deactivated"):
                service.login("unit.login3@example.com", "Citizen@123")

    def test_login_blocked_during_maintenance_mode_for_non_admin(self, app):
        with app.app_context():
            _make_citizen("unit.login4@example.com")
            setting = SystemSettingsService.get_settings()
            setting.maintenance_mode = True
            db.session.commit()
            try:
                service = AuthService()
                with pytest.raises(ValueError, match="maintenance"):
                    service.login("unit.login4@example.com", "Citizen@123")
            finally:
                setting.maintenance_mode = False
                db.session.commit()


class TestAuthServiceTokenAndProfile:
    """Unit tests for refresh_token, get_current_user, update_profile,
    change_password, and update_avatar."""

    def test_refresh_token_issues_new_access_token(self, app):
        with app.app_context():
            user = _make_citizen("unit.refresh1@example.com")
            service = AuthService()
            result = service.refresh_token(user.id)
            assert "access_token" in result
            assert result["token_type"] == "Bearer"

    def test_refresh_token_rejects_unknown_user(self, app):
        with app.app_context():
            service = AuthService()
            with pytest.raises(ValueError, match="not found"):
                service.refresh_token(999999)

    def test_refresh_token_rejects_inactive_user(self, app):
        with app.app_context():
            user = _make_citizen("unit.refresh2@example.com", is_active=False)
            service = AuthService()
            with pytest.raises(ValueError, match="inactive"):
                service.refresh_token(user.id)

    def test_get_current_user_returns_profile(self, app):
        with app.app_context():
            user = _make_citizen("unit.me1@example.com")
            service = AuthService()
            result = service.get_current_user(user.id)
            assert result["user"]["id"] == user.id

    def test_get_current_user_rejects_unknown_id(self, app):
        with app.app_context():
            service = AuthService()
            with pytest.raises(ValueError, match="not found"):
                service.get_current_user(999999)

    def test_update_profile_changes_editable_fields(self, app):
        with app.app_context():
            user = _make_citizen("unit.updateprofile1@example.com")
            service = AuthService()
            result = service.update_profile(user.id, {
                "first_name": "Changed",
                "last_name": "Name",
                "phone": "+91-9876500000",
            })
            assert result["user"]["first_name"] == "Changed"
            assert result["user"]["phone"] == "+91-9876500000"

    def test_change_password_succeeds_with_correct_current_password(self, app):
        with app.app_context():
            user = _make_citizen("unit.changepw1@example.com")
            service = AuthService()
            service.change_password(user.id, {
                "current_password": "Citizen@123",
                "new_password": "NewCitizen@456",
            })
            refreshed = User.query.get(user.id)
            assert refreshed.check_password("NewCitizen@456") is True

    def test_change_password_rejects_wrong_current_password(self, app):
        with app.app_context():
            user = _make_citizen("unit.changepw2@example.com")
            service = AuthService()
            with pytest.raises(ValueError, match="Current password is incorrect"):
                service.change_password(user.id, {
                    "current_password": "WrongOldPass",
                    "new_password": "NewCitizen@456",
                })

    def test_update_avatar_sets_avatar_url(self, app):
        with app.app_context():
            user = _make_citizen("unit.avatar1@example.com")
            service = AuthService()
            result = service.update_avatar(user.id, "/api/v1/auth/me/avatar/photo.jpg")
            assert result["user"]["avatar_url"] == "/api/v1/auth/me/avatar/photo.jpg"


class TestAuthServiceResolveCityId:
    """Unit tests for AuthService._resolve_city_id, exercised via registration."""

    def test_resolve_city_id_rejects_mismatched_explicit_city(self, app):
        with app.app_context():
            other_city = City.query.filter_by(name="OtherCityAuthUnit").first()
            if not other_city:
                other_city = City(name="OtherCityAuthUnit", is_active=True)
                db.session.add(other_city)
                db.session.commit()

            service = AuthService()
            with pytest.raises(ValueError, match="does not match"):
                service.register_user({
                    "username": "unit_register_5",
                    "email": "unit.register5@example.com",
                    "password": "Citizen@123",
                    "first_name": "Unit",
                    "last_name": "Tester",
                    "pincode": "226001",
                    "city_id": other_city.id,
                })
