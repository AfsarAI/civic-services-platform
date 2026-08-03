"""
Integration tests for duplicate-complaint detection: the admin "possible
duplicates nearby" + "mark as duplicate" endpoints, the citizen pre-submission
advisory check endpoint, and the configurable detection radius in system
settings.
"""

from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.city import City
from app.models.role import Role
from app.models.user import User

BASE_LAT, BASE_LON = 26.8467, 80.9462


def _ensure_system_admin(email: str) -> User:
    role = Role.query.filter_by(name=Role.ADMINISTRATOR).first()
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(
        username=email.split("@")[0], email=email, first_name="System",
        last_name="Admin", role_id=role.id, is_active=True,
    )
    user.set_password("Admin@123456")
    db.session.add(user)
    db.session.flush()
    db.session.add(AdministratorProfile(
        user_id=user.id, admin_level=AdministratorProfile.SYSTEM, city_id=None, created_by_id=None,
    ))
    db.session.commit()
    return user


def _ensure_municipal_admin(email: str, city_name: str) -> User:
    role = Role.query.filter_by(name=Role.ADMINISTRATOR).first()
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    city = City.query.filter_by(name=city_name).first()
    if not city:
        city = City(name=city_name, is_active=True)
        db.session.add(city)
        db.session.flush()
    user = User(
        username=email.split("@")[0], email=email, first_name="Municipal",
        last_name="Admin", role_id=role.id, city_id=city.id, is_active=True,
    )
    user.set_password("Admin@123456")
    db.session.add(user)
    db.session.flush()
    db.session.add(AdministratorProfile(
        user_id=user.id, admin_level=AdministratorProfile.MUNICIPAL, city_id=city.id, created_by_id=None,
    ))
    db.session.commit()
    return user


def _login(client, email: str, password: str = "Admin@123456") -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.get_json()["data"]["access_token"]


def _register_and_login_citizen(client, email: str) -> dict:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": email.split("@")[0],
            "email": email,
            "password": "Password123!",
            "first_name": "Citizen",
            "last_name": "Tester",
            "pincode": "226001",
        },
    )
    assert register_response.status_code == 201
    login_response = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    assert login_response.status_code == 200
    return login_response.get_json()["data"]


def _submit_complaint(client, citizen_token: str, city_id: int, latitude: float, longitude: float) -> int:
    response = client.post(
        "/api/v1/citizen/complaints",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={
            "title": "Pothole for duplicate detection integration test",
            "description": "A pothole complaint used to test duplicate detection.",
            "category": "pothole",
            "city_id": city_id,
            "latitude": latitude,
            "longitude": longitude,
            "image_url": "/api/v1/citizen/complaints/media/test-photo.jpg",
        },
    )
    assert response.status_code == 201
    return response.get_json()["data"]["complaint"]["id"]


class TestAdminDuplicateCandidates:
    """Integration tests for GET /admin/complaints/<id>/duplicates."""

    def test_finds_nearby_open_complaint(self, app, client):
        _ensure_system_admin("dup-sysadmin1@example.com")
        admin_token = _login(client, "dup-sysadmin1@example.com")
        citizen_auth = _register_and_login_citizen(client, "dup-citizen1@example.com")
        city_id = citizen_auth["user"]["city_id"]

        target_id = _submit_complaint(client, citizen_auth["access_token"], city_id, BASE_LAT, BASE_LON)
        nearby_id = _submit_complaint(
            client, citizen_auth["access_token"], city_id, BASE_LAT + 0.0001, BASE_LON
        )

        response = client.get(
            f"/api/v1/admin/complaints/{target_id}/duplicates?radius_meters=50",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        candidate_ids = [c["id"] for c in response.get_json()["data"]["candidates"]]
        assert nearby_id in candidate_ids
        assert target_id not in candidate_ids

    def test_returns_404_for_missing_complaint(self, app, client):
        _ensure_system_admin("dup-sysadmin2@example.com")
        admin_token = _login(client, "dup-sysadmin2@example.com")
        response = client.get(
            "/api/v1/admin/complaints/999999/duplicates",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_municipal_admin_scoped_to_own_city(self, app, client):
        _ensure_municipal_admin("dup-muniadmin1@example.com", "DupCityA")
        admin_token = _login(client, "dup-muniadmin1@example.com")
        citizen_auth = _register_and_login_citizen(client, "dup-citizen2@example.com")

        with app.app_context():
            other_city = City.query.filter_by(name="DupCityB").first()
            if not other_city:
                other_city = City(name="DupCityB", is_active=True)
                db.session.add(other_city)
                db.session.commit()
            other_city_id = other_city.id

        target_id = _submit_complaint(
            client, citizen_auth["access_token"], other_city_id, BASE_LAT, BASE_LON
        )
        response = client.get(
            f"/api/v1/admin/complaints/{target_id}/duplicates",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404


class TestAdminMarkDuplicate:
    """Integration tests for POST /admin/complaints/<id>/mark-duplicate."""

    def test_marks_complaint_as_duplicate_and_notifies_citizen(self, app, client):
        _ensure_system_admin("dup-sysadmin3@example.com")
        admin_token = _login(client, "dup-sysadmin3@example.com")
        citizen_auth = _register_and_login_citizen(client, "dup-citizen3@example.com")
        city_id = citizen_auth["user"]["city_id"]

        primary_id = _submit_complaint(client, citizen_auth["access_token"], city_id, BASE_LAT, BASE_LON)
        duplicate_id = _submit_complaint(
            client, citizen_auth["access_token"], city_id, BASE_LAT + 0.0001, BASE_LON
        )

        response = client.post(
            f"/api/v1/admin/complaints/{duplicate_id}/mark-duplicate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"duplicate_of_id": primary_id, "reason": "Same pothole"},
        )
        assert response.status_code == 200
        data = response.get_json()["data"]["complaint"]
        assert data["status"] == "rejected"
        assert data["duplicate_of_id"] == primary_id

        notif_response = client.get(
            "/api/v1/notifications/",
            headers={"Authorization": f"Bearer {citizen_auth['access_token']}"},
        )
        messages = [n["message"] for n in notif_response.get_json()["data"]["items"]]
        assert any("duplicate" in m.lower() for m in messages)

    def test_rejects_self_reference(self, app, client):
        _ensure_system_admin("dup-sysadmin4@example.com")
        admin_token = _login(client, "dup-sysadmin4@example.com")
        citizen_auth = _register_and_login_citizen(client, "dup-citizen4@example.com")
        complaint_id = _submit_complaint(
            client, citizen_auth["access_token"], citizen_auth["user"]["city_id"], BASE_LAT, BASE_LON
        )

        response = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/mark-duplicate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"duplicate_of_id": complaint_id},
        )
        assert response.status_code == 400

    def test_rejects_missing_duplicate_of_id_with_400(self, app, client):
        _ensure_system_admin("dup-sysadmin5@example.com")
        admin_token = _login(client, "dup-sysadmin5@example.com")
        citizen_auth = _register_and_login_citizen(client, "dup-citizen5@example.com")
        complaint_id = _submit_complaint(
            client, citizen_auth["access_token"], citizen_auth["user"]["city_id"], BASE_LAT, BASE_LON
        )

        response = client.post(
            f"/api/v1/admin/complaints/{complaint_id}/mark-duplicate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={},
        )
        # Flask-RESTX's own swagger-model validation (required=True on
        # duplicate_of_id) runs before the Marshmallow schema and returns 400,
        # not 422 — see gotcha #22 in the project docs.
        assert response.status_code == 400

    def test_non_admin_cannot_mark_duplicate(self, app, client):
        citizen_auth = _register_and_login_citizen(client, "dup-citizen6@example.com")
        response = client.post(
            "/api/v1/admin/complaints/1/mark-duplicate",
            headers={"Authorization": f"Bearer {citizen_auth['access_token']}"},
            json={"duplicate_of_id": 2},
        )
        assert response.status_code == 403


class TestCitizenNearbyDuplicatesCheck:
    """Integration tests for GET /citizen/complaints/nearby-duplicates."""

    def test_finds_nearby_open_complaint(self, app, client):
        citizen_auth = _register_and_login_citizen(client, "dup-citizen7@example.com")
        _submit_complaint(
            client, citizen_auth["access_token"], citizen_auth["user"]["city_id"], BASE_LAT, BASE_LON
        )

        response = client.get(
            "/api/v1/citizen/complaints/nearby-duplicates"
            f"?latitude={BASE_LAT + 0.0001}&longitude={BASE_LON}&radius_meters=50",
            headers={"Authorization": f"Bearer {citizen_auth['access_token']}"},
        )
        assert response.status_code == 200
        assert len(response.get_json()["data"]["candidates"]) >= 1
        # Advisory response must not leak other citizens' identity.
        assert "citizen_id" not in response.get_json()["data"]["candidates"][0]

    def test_returns_empty_when_nothing_nearby(self, app, client):
        citizen_auth = _register_and_login_citizen(client, "dup-citizen8@example.com")
        response = client.get(
            "/api/v1/citizen/complaints/nearby-duplicates?latitude=1.0&longitude=1.0",
            headers={"Authorization": f"Bearer {citizen_auth['access_token']}"},
        )
        assert response.status_code == 200
        assert response.get_json()["data"]["candidates"] == []

    def test_missing_coordinates_returns_400(self, app, client):
        citizen_auth = _register_and_login_citizen(client, "dup-citizen9@example.com")
        response = client.get(
            "/api/v1/citizen/complaints/nearby-duplicates",
            headers={"Authorization": f"Bearer {citizen_auth['access_token']}"},
        )
        assert response.status_code == 400

    def test_invalid_coordinates_returns_400(self, app, client):
        citizen_auth = _register_and_login_citizen(client, "dup-citizen10@example.com")
        response = client.get(
            "/api/v1/citizen/complaints/nearby-duplicates?latitude=999&longitude=999",
            headers={"Authorization": f"Bearer {citizen_auth['access_token']}"},
        )
        assert response.status_code == 400

    def test_requires_authentication(self, app, client):
        response = client.get(
            "/api/v1/citizen/complaints/nearby-duplicates?latitude=1.0&longitude=1.0",
        )
        assert response.status_code == 401


class TestSystemSettingsDuplicateRadius:
    """Integration test for the configurable duplicate-detection radius."""

    def test_system_admin_can_update_duplicate_radius(self, app, client):
        _ensure_system_admin("dup-sysadmin-settings@example.com")
        admin_token = _login(client, "dup-sysadmin-settings@example.com")

        response = client.put(
            "/api/v1/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"duplicate_detection_radius_meters": 100},
        )
        assert response.status_code == 200
        assert response.get_json()["data"]["settings"]["duplicate_detection_radius_meters"] == 100

        # Reset for other tests relying on the default 50m radius.
        client.put(
            "/api/v1/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"duplicate_detection_radius_meters": 50},
        )
