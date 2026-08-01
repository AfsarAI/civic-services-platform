"""
Unit tests for CitizenService — isolated from HTTP plumbing, calling the
service layer directly against the real (in-memory) database.
"""

import pytest
from app.api.citizen.service import CitizenService
from app.extensions import db
from app.models.city import City
from app.models.complaint import Complaint
from app.models.role import Role
from app.models.user import User


def _make_citizen(email: str, city_id: int = None, pincode: str = "226001") -> User:
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
        city_id=city_id,
        pincode=pincode,
        is_active=True,
    )
    user.set_password("Citizen@123")
    db.session.add(user)
    db.session.commit()
    return user


def _make_complaint(citizen_id: int, status: str = Complaint.STATUS_PENDING, **kwargs) -> Complaint:
    complaint = Complaint(
        citizen_id=citizen_id,
        title=kwargs.get("title", "Pothole on Main Street"),
        description=kwargs.get("description", "A deep pothole causing traffic issues."),
        category=Complaint.CATEGORY_POTHOLE,
        status=status,
        priority=kwargs.get("priority", "medium"),
    )
    db.session.add(complaint)
    db.session.commit()
    return complaint


class TestCitizenServiceSubmitComplaint:
    """Unit tests for CitizenService.submit_complaint."""

    def test_submit_complaint_creates_pending_complaint(self, app):
        with app.app_context():
            citizen = _make_citizen("unit.citizen.submit1@example.com")
            service = CitizenService()
            result = service.submit_complaint(citizen.id, {
                "title": "Large pothole",
                "description": "There is a large pothole causing damage.",
                "pincode": "226001",
            })
            assert result["complaint"]["status"] == Complaint.STATUS_PENDING
            assert result["complaint"]["citizen_id"] == citizen.id

    def test_submit_complaint_rejects_unknown_citizen(self, app):
        with app.app_context():
            service = CitizenService()
            with pytest.raises(ValueError, match="not found"):
                service.submit_complaint(999999, {
                    "title": "Large pothole",
                    "description": "There is a large pothole causing damage.",
                    "pincode": "226001",
                })


class TestCitizenServiceListAndGetComplaints:
    """Unit tests for get_my_complaints and get_complaint."""

    def test_get_my_complaints_returns_only_own_complaints(self, app):
        with app.app_context():
            citizen = _make_citizen("unit.citizen.list1@example.com")
            other = _make_citizen("unit.citizen.list2@example.com")
            _make_complaint(citizen.id, title="Mine")
            _make_complaint(other.id, title="Not mine")
            service = CitizenService()
            result = service.get_my_complaints(citizen.id)
            assert all(item["citizen_id"] == citizen.id for item in result["items"])

    def test_get_my_complaints_filters_by_status(self, app):
        with app.app_context():
            citizen = _make_citizen("unit.citizen.list3@example.com")
            _make_complaint(citizen.id, status=Complaint.STATUS_PENDING)
            _make_complaint(citizen.id, status=Complaint.STATUS_RESOLVED)
            service = CitizenService()
            result = service.get_my_complaints(citizen.id, status=Complaint.STATUS_RESOLVED)
            assert all(item["status"] == Complaint.STATUS_RESOLVED for item in result["items"])

    def test_get_my_complaints_rejects_invalid_status(self, app):
        with app.app_context():
            citizen = _make_citizen("unit.citizen.list4@example.com")
            service = CitizenService()
            with pytest.raises(ValueError, match="Invalid status"):
                service.get_my_complaints(citizen.id, status="not-a-status")

    def test_get_complaint_returns_owned_complaint(self, app):
        with app.app_context():
            citizen = _make_citizen("unit.citizen.get1@example.com")
            complaint = _make_complaint(citizen.id)
            service = CitizenService()
            result = service.get_complaint(complaint.id, citizen.id)
            assert result["complaint"]["id"] == complaint.id

    def test_get_complaint_rejects_other_citizens_complaint(self, app):
        with app.app_context():
            owner = _make_citizen("unit.citizen.get2@example.com")
            other = _make_citizen("unit.citizen.get3@example.com")
            complaint = _make_complaint(owner.id)
            service = CitizenService()
            with pytest.raises(ValueError, match="permission"):
                service.get_complaint(complaint.id, other.id)

    def test_get_complaint_rejects_missing_complaint(self, app):
        with app.app_context():
            citizen = _make_citizen("unit.citizen.get4@example.com")
            service = CitizenService()
            with pytest.raises(ValueError, match="not found"):
                service.get_complaint(999999, citizen.id)


class TestCitizenServiceUpdateAndCancelComplaint:
    """Unit tests for update_complaint and cancel_complaint."""

    def test_update_complaint_edits_pending_complaint(self, app):
        with app.app_context():
            citizen = _make_citizen("unit.citizen.update1@example.com")
            complaint = _make_complaint(citizen.id)
            service = CitizenService()
            result = service.update_complaint(complaint.id, citizen.id, {"title": "Updated title"})
            assert result["complaint"]["title"] == "Updated title"

    def test_update_complaint_rejects_non_pending_complaint(self, app):
        with app.app_context():
            citizen = _make_citizen("unit.citizen.update2@example.com")
            complaint = _make_complaint(citizen.id, status=Complaint.STATUS_ASSIGNED)
            service = CitizenService()
            with pytest.raises(ValueError, match="Only pending complaints can be edited"):
                service.update_complaint(complaint.id, citizen.id, {"title": "New title"})

    def test_cancel_complaint_soft_cancels_pending_complaint(self, app):
        with app.app_context():
            citizen = _make_citizen("unit.citizen.cancel1@example.com")
            complaint = _make_complaint(citizen.id)
            service = CitizenService()
            result = service.cancel_complaint(complaint.id, citizen.id)
            assert result["complaint"]["status"] == Complaint.STATUS_CANCELLED
            # Row is preserved, not deleted.
            assert Complaint.query.get(complaint.id) is not None

    def test_cancel_complaint_rejects_non_pending_complaint(self, app):
        with app.app_context():
            citizen = _make_citizen("unit.citizen.cancel2@example.com")
            complaint = _make_complaint(citizen.id, status=Complaint.STATUS_IN_PROGRESS)
            service = CitizenService()
            with pytest.raises(ValueError, match="Only pending complaints can be cancelled"):
                service.cancel_complaint(complaint.id, citizen.id)


class TestCitizenServiceFeedback:
    """Unit tests for submit_feedback."""

    def test_submit_feedback_accepted_for_resolved_complaint(self, app):
        with app.app_context():
            citizen = _make_citizen("unit.citizen.feedback1@example.com")
            complaint = _make_complaint(citizen.id, status=Complaint.STATUS_RESOLVED)
            service = CitizenService()
            result = service.submit_feedback(complaint.id, citizen.id, {
                "rating": 5,
                "comment": "Great work!",
            })
            assert result["feedback"]["rating"] == 5

    def test_submit_feedback_rejected_for_pending_complaint(self, app):
        with app.app_context():
            citizen = _make_citizen("unit.citizen.feedback2@example.com")
            complaint = _make_complaint(citizen.id, status=Complaint.STATUS_PENDING)
            service = CitizenService()
            with pytest.raises(ValueError, match="resolved or closed"):
                service.submit_feedback(complaint.id, citizen.id, {"rating": 4})

    def test_submit_feedback_rejects_duplicate_feedback(self, app):
        with app.app_context():
            citizen = _make_citizen("unit.citizen.feedback3@example.com")
            complaint = _make_complaint(citizen.id, status=Complaint.STATUS_RESOLVED)
            service = CitizenService()
            service.submit_feedback(complaint.id, citizen.id, {"rating": 5})
            with pytest.raises(ValueError, match="already been submitted"):
                service.submit_feedback(complaint.id, citizen.id, {"rating": 3})


class TestCitizenServiceDashboard:
    """Unit tests for get_dashboard_summary."""

    def test_dashboard_summary_returns_counts_by_status(self, app):
        with app.app_context():
            citizen = _make_citizen("unit.citizen.dashboard1@example.com")
            _make_complaint(citizen.id, status=Complaint.STATUS_PENDING)
            _make_complaint(citizen.id, status=Complaint.STATUS_RESOLVED)
            service = CitizenService()
            result = service.get_dashboard_summary(citizen.id)
            assert result["total_complaints"] >= 2
            assert result["by_status"][Complaint.STATUS_PENDING] >= 1
            assert result["by_status"][Complaint.STATUS_RESOLVED] >= 1


class TestCitizenServiceResolveComplaintCity:
    """Unit tests for _resolve_complaint_city, exercised via submit_complaint."""

    def test_submit_complaint_with_city_id_only(self, app):
        with app.app_context():
            city = City.query.filter_by(name="Lucknow").first()
            citizen = _make_citizen("unit.citizen.cityid1@example.com", city_id=None, pincode=None)
            service = CitizenService()
            result = service.submit_complaint(citizen.id, {
                "title": "Pothole via city_id",
                "description": "Submitted using only a city_id, no pincode.",
                "city_id": city.id,
            })
            assert result["complaint"]["city_id"] == city.id

    def test_submit_complaint_rejects_invalid_city_id(self, app):
        with app.app_context():
            citizen = _make_citizen("unit.citizen.cityid2@example.com", city_id=None, pincode=None)
            service = CitizenService()
            with pytest.raises(ValueError, match="not valid"):
                service.submit_complaint(citizen.id, {
                    "title": "Pothole via bad city_id",
                    "description": "Submitted using an invalid city_id.",
                    "city_id": 999999,
                })

    def test_submit_complaint_rejects_pincode_city_mismatch(self, app):
        with app.app_context():
            other_city = City.query.filter_by(name="OtherCityCitizenUnit").first()
            if not other_city:
                other_city = City(name="OtherCityCitizenUnit", is_active=True)
                db.session.add(other_city)
                db.session.commit()
            citizen = _make_citizen("unit.citizen.cityid3@example.com", city_id=None, pincode=None)
            service = CitizenService()
            with pytest.raises(ValueError, match="does not match"):
                service.submit_complaint(citizen.id, {
                    "title": "Pothole mismatch",
                    "description": "Pincode maps to a different city than city_id.",
                    "pincode": "226001",
                    "city_id": other_city.id,
                })
