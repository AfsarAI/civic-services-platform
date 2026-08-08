"""
Unit tests for DuplicateDetectionService — nearby open-complaint lookup
shared by both the citizen submission flow and admin review flow.
"""

from app.extensions import db
from app.models.complaint import Complaint
from app.models.city import City
from app.models.role import Role
from app.models.user import User
from app.services.duplicate_detection_service import DuplicateDetectionService

BASE_LAT, BASE_LON = 26.8467, 80.9462


def _ensure_citizen(email: str) -> User:
    role = Role.query.filter_by(name=Role.CITIZEN).first()
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(
        username=email.split("@")[0], email=email, first_name="Test",
        last_name="Citizen", role_id=role.id, is_active=True,
    )
    user.set_password("Citizen@123")
    db.session.add(user)
    db.session.commit()
    return user


def _make_complaint(
    citizen_id, latitude=BASE_LAT, longitude=BASE_LON,
    status=Complaint.STATUS_PENDING, city_id=None, duplicate_of_id=None,
) -> Complaint:
    complaint = Complaint(
        citizen_id=citizen_id, title="Pothole for duplicate detection unit tests",
        description="A complaint used to test nearby-duplicate detection.",
        category=Complaint.CATEGORY_POTHOLE, status=status, priority="medium",
        latitude=latitude, longitude=longitude, city_id=city_id,
        duplicate_of_id=duplicate_of_id,
    )
    db.session.add(complaint)
    db.session.commit()
    return complaint


class TestFindNearbyOpenComplaints:
    """Unit tests for DuplicateDetectionService.find_nearby_open_complaints."""

    def test_finds_complaint_within_radius(self, app):
        with app.app_context():
            citizen = _ensure_citizen("unit.dup.citizen1@example.com")
            nearby = _make_complaint(citizen.id, latitude=BASE_LAT + 0.0002, longitude=BASE_LON)

            pairs = DuplicateDetectionService.find_nearby_open_complaints(
                BASE_LAT, BASE_LON, radius_meters=50
            )
            ids = [c.id for _, c in pairs]
            assert nearby.id in ids

    def test_excludes_complaint_outside_radius(self, app):
        with app.app_context():
            citizen = _ensure_citizen("unit.dup.citizen2@example.com")
            far_away = _make_complaint(citizen.id, latitude=BASE_LAT + 0.01, longitude=BASE_LON)

            pairs = DuplicateDetectionService.find_nearby_open_complaints(
                BASE_LAT, BASE_LON, radius_meters=50
            )
            ids = [c.id for _, c in pairs]
            assert far_away.id not in ids

    def test_excludes_terminal_status_complaints(self, app):
        with app.app_context():
            citizen = _ensure_citizen("unit.dup.citizen3@example.com")
            resolved = _make_complaint(
                citizen.id, latitude=BASE_LAT + 0.0001, longitude=BASE_LON,
                status=Complaint.STATUS_RESOLVED,
            )
            pairs = DuplicateDetectionService.find_nearby_open_complaints(
                BASE_LAT, BASE_LON, radius_meters=50
            )
            ids = [c.id for _, c in pairs]
            assert resolved.id not in ids

    def test_excludes_already_linked_duplicates(self, app):
        with app.app_context():
            citizen = _ensure_citizen("unit.dup.citizen4@example.com")
            primary = _make_complaint(citizen.id, latitude=BASE_LAT, longitude=BASE_LON)
            already_duplicate = _make_complaint(
                citizen.id, latitude=BASE_LAT + 0.0001, longitude=BASE_LON,
                duplicate_of_id=primary.id,
            )
            pairs = DuplicateDetectionService.find_nearby_open_complaints(
                BASE_LAT, BASE_LON, radius_meters=50
            )
            ids = [c.id for _, c in pairs]
            assert already_duplicate.id not in ids

    def test_excludes_self_when_given(self, app):
        with app.app_context():
            citizen = _ensure_citizen("unit.dup.citizen5@example.com")
            target = _make_complaint(citizen.id)
            pairs = DuplicateDetectionService.find_nearby_open_complaints(
                BASE_LAT, BASE_LON, radius_meters=50, exclude_complaint_id=target.id
            )
            ids = [c.id for _, c in pairs]
            assert target.id not in ids

    def test_results_sorted_nearest_first(self, app):
        with app.app_context():
            citizen = _ensure_citizen("unit.dup.citizen6@example.com")
            far = _make_complaint(citizen.id, latitude=BASE_LAT + 0.0003, longitude=BASE_LON)
            near = _make_complaint(citizen.id, latitude=BASE_LAT + 0.0001, longitude=BASE_LON)

            pairs = DuplicateDetectionService.find_nearby_open_complaints(
                BASE_LAT, BASE_LON, radius_meters=100
            )
            ids_in_order = [c.id for _, c in pairs]
            assert ids_in_order.index(near.id) < ids_in_order.index(far.id)

    def test_scopes_to_city_when_provided(self, app):
        with app.app_context():
            city_a = (
                City.query.filter_by(name="DupDetectCityA").first()
                or City(name="DupDetectCityA", is_active=True)
            )
            if not city_a.id:
                db.session.add(city_a)
                db.session.commit()
            city_b = (
                City.query.filter_by(name="DupDetectCityB").first()
                or City(name="DupDetectCityB", is_active=True)
            )
            if not city_b.id:
                db.session.add(city_b)
                db.session.commit()

            citizen = _ensure_citizen("unit.dup.citizen7@example.com")
            in_city_b = _make_complaint(
                citizen.id, latitude=BASE_LAT + 0.0001, longitude=BASE_LON, city_id=city_b.id
            )

            pairs = DuplicateDetectionService.find_nearby_open_complaints(
                BASE_LAT, BASE_LON, radius_meters=50, city_id=city_a.id
            )
            ids = [c.id for _, c in pairs]
            assert in_city_b.id not in ids

    def test_default_radius_uses_system_setting(self, app):
        with app.app_context():
            radius = DuplicateDetectionService.default_radius_meters()
            assert radius == 50
