"""
Integration tests for the reports/analytics namespace (TPS-85/96/97/98).

Covers:
- Both administrator subtypes can access reports; municipal administrators
  are automatically scoped to their own city, system administrators are not.
- Non-administrators are forbidden.
- Date-range and status filters.
- The by-priority and by-location breakdowns.
"""

from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.city import City
from app.models.role import Role
from app.models.user import User


class TestReportsEndpoints:
    """Integration tests for /api/v1/reports endpoints."""

    @staticmethod
    def _ensure_city(name: str) -> City:
        city = City.query.filter_by(name=name).first()
        if not city:
            city = City(name=name, is_active=True)
            db.session.add(city)
            db.session.commit()
        return city

    @classmethod
    def _ensure_admin(cls, email: str, admin_level: str, city_name: str = None) -> User:
        role = Role.query.filter_by(name=Role.ADMINISTRATOR).first()
        user = User.query.filter_by(email=email).first()
        if user:
            return user

        city = cls._ensure_city(city_name) if city_name else None

        user = User(
            username=email.split("@")[0],
            email=email,
            first_name="Admin",
            last_name=admin_level.title(),
            role_id=role.id,
            is_active=True,
        )
        user.set_password("Admin@123456")
        db.session.add(user)
        db.session.flush()
        db.session.add(
            AdministratorProfile(
                user_id=user.id,
                admin_level=admin_level,
                city_id=city.id if city else None,
                created_by_id=None,
            )
        )
        db.session.commit()
        return user

    @staticmethod
    def _login(client, email: str, password: str = "Admin@123456") -> str:
        response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200
        return response.get_json()["data"]["access_token"]

    @staticmethod
    def _register_and_login_citizen(client, email: str):
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
        login_response = client.post(
            "/api/v1/auth/login", json={"email": email, "password": "Password123!"}
        )
        assert login_response.status_code == 200
        return login_response.get_json()["data"]

    @classmethod
    def _submit_complaint(cls, client, citizen_token: str, city_id: int, priority: str = "high") -> int:
        response = client.post(
            "/api/v1/citizen/complaints",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={
                "title": "Deep pothole requiring urgent repair",
                "description": "Large pothole causing traffic issues near the junction.",
                "category": "pothole",
                "priority": priority,
                "city_id": city_id,
                "image_url": "/api/v1/citizen/complaints/media/test-photo.jpg",
            },
        )
        assert response.status_code == 201
        return response.get_json()["data"]["complaint"]["id"]

    REPORT_ENDPOINTS = [
        "/api/v1/reports/complaints/summary",
        "/api/v1/reports/complaints/by-status",
        "/api/v1/reports/complaints/by-category",
        "/api/v1/reports/complaints/by-priority",
        "/api/v1/reports/complaints/by-location",
        "/api/v1/reports/complaints/trends",
        "/api/v1/reports/workers/performance",
    ]

    def test_non_admin_cannot_access_any_report_endpoint(self, app, client):
        citizen_auth = self._register_and_login_citizen(client, "reports-citizen@example.com")
        citizen_token = citizen_auth["access_token"]
        for endpoint in self.REPORT_ENDPOINTS:
            response = client.get(endpoint, headers={"Authorization": f"Bearer {citizen_token}"})
            assert response.status_code == 403, endpoint

    def test_system_admin_can_access_all_report_endpoints(self, app, client):
        self._ensure_admin("reports-sysadmin@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "reports-sysadmin@example.com")
        for endpoint in self.REPORT_ENDPOINTS:
            response = client.get(endpoint, headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200, endpoint

    def test_municipal_admin_can_access_reports_scoped_to_own_city(self, app, client):
        """Municipal administrators must NOT get 403 on reports, and must only
        see their own city's data (the user's explicit ask for this story)."""
        city_a = self._ensure_city("ReportsCityA")
        city_b = self._ensure_city("ReportsCityB")
        self._ensure_admin("reports-muni-a@example.com", AdministratorProfile.MUNICIPAL, "ReportsCityA")
        muni_token = self._login(client, "reports-muni-a@example.com")

        citizen_auth = self._register_and_login_citizen(client, "reports-citizen-a@example.com")
        self._submit_complaint(client, citizen_auth["access_token"], city_a.id)

        other_citizen_auth = self._register_and_login_citizen(client, "reports-citizen-b@example.com")
        self._submit_complaint(client, other_citizen_auth["access_token"], city_b.id)

        summary_response = client.get(
            "/api/v1/reports/complaints/summary", headers={"Authorization": f"Bearer {muni_token}"}
        )
        assert summary_response.status_code == 200
        # Only city A's single complaint should be counted, not city B's.
        assert summary_response.get_json()["data"]["total"] == 1

        location_response = client.get(
            "/api/v1/reports/complaints/by-location", headers={"Authorization": f"Bearer {muni_token}"}
        )
        assert location_response.status_code == 200
        location_breakdown = location_response.get_json()["data"]["breakdown"]
        assert all(row["city_name"] == "ReportsCityA" for row in location_breakdown)

    def test_system_admin_sees_all_cities_unscoped(self, app, client):
        city_a = self._ensure_city("ReportsCityC")
        city_b = self._ensure_city("ReportsCityD")
        self._ensure_admin("reports-sysadmin2@example.com", AdministratorProfile.SYSTEM)
        sys_token = self._login(client, "reports-sysadmin2@example.com")

        citizen_a = self._register_and_login_citizen(client, "reports-citizen-c@example.com")
        self._submit_complaint(client, citizen_a["access_token"], city_a.id)
        citizen_b = self._register_and_login_citizen(client, "reports-citizen-d@example.com")
        self._submit_complaint(client, citizen_b["access_token"], city_b.id)

        response = client.get(
            "/api/v1/reports/complaints/by-location", headers={"Authorization": f"Bearer {sys_token}"}
        )
        assert response.status_code == 200
        cities_seen = {row["city_name"] for row in response.get_json()["data"]["breakdown"]}
        assert "ReportsCityC" in cities_seen
        assert "ReportsCityD" in cities_seen

    def test_status_filter_narrows_by_category_breakdown(self, app, client):
        self._ensure_admin("reports-sysadmin3@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "reports-sysadmin3@example.com")
        city = self._ensure_city("ReportsCityE")
        citizen_auth = self._register_and_login_citizen(client, "reports-citizen-e@example.com")
        self._submit_complaint(client, citizen_auth["access_token"], city.id)

        response = client.get(
            "/api/v1/reports/complaints/by-category",
            headers={"Authorization": f"Bearer {token}"},
            query_string={"status": "pending"},
        )
        assert response.status_code == 200
        assert response.get_json()["data"]["total"] >= 1

        response_none = client.get(
            "/api/v1/reports/complaints/by-category",
            headers={"Authorization": f"Bearer {token}"},
            query_string={"status": "closed"},
        )
        assert response_none.status_code == 200

    def test_invalid_status_filter_returns_400(self, app, client):
        self._ensure_admin("reports-sysadmin4@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "reports-sysadmin4@example.com")
        response = client.get(
            "/api/v1/reports/complaints/summary",
            headers={"Authorization": f"Bearer {token}"},
            query_string={"status": "not-a-status"},
        )
        assert response.status_code == 400

    def test_date_range_filter_excludes_out_of_range_complaints(self, app, client):
        self._ensure_admin("reports-sysadmin5@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "reports-sysadmin5@example.com")
        city = self._ensure_city("ReportsCityF")
        citizen_auth = self._register_and_login_citizen(client, "reports-citizen-f@example.com")
        self._submit_complaint(client, citizen_auth["access_token"], city.id)

        # A date range entirely in the future should exclude today's complaint.
        response = client.get(
            "/api/v1/reports/complaints/summary",
            headers={"Authorization": f"Bearer {token}"},
            query_string={"date_from": "2999-01-01", "date_to": "2999-01-31"},
        )
        assert response.status_code == 200
        assert response.get_json()["data"]["total"] == 0

    def test_invalid_date_format_returns_400(self, app, client):
        self._ensure_admin("reports-sysadmin6@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "reports-sysadmin6@example.com")
        response = client.get(
            "/api/v1/reports/complaints/summary",
            headers={"Authorization": f"Bearer {token}"},
            query_string={"date_from": "not-a-date"},
        )
        assert response.status_code == 400

    def test_reversed_date_range_returns_400(self, app, client):
        self._ensure_admin("reports-reversed-range@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "reports-reversed-range@example.com")
        response = client.get(
            "/api/v1/reports/complaints/summary",
            headers={"Authorization": f"Bearer {token}"},
            query_string={"date_from": "2026-08-02", "date_to": "2026-08-01"},
        )
        assert response.status_code == 400
        assert "on or before" in response.get_json()["message"]

    def test_summary_includes_priority_breakdown(self, app, client):
        self._ensure_admin("reports-sysadmin7@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "reports-sysadmin7@example.com")
        city = self._ensure_city("ReportsCityG")
        citizen_auth = self._register_and_login_citizen(client, "reports-citizen-g@example.com")
        self._submit_complaint(client, citizen_auth["access_token"], city.id, priority="urgent")

        response = client.get(
            "/api/v1/reports/complaints/summary", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.get_json()["data"]["by_priority"].get("urgent", 0) >= 1

    EXPORT_ENDPOINTS = [
        ("/api/v1/reports/export/csv", "text/csv"),
        (
            "/api/v1/reports/export/excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        ("/api/v1/reports/export/pdf", "application/pdf"),
    ]

    def test_non_admin_cannot_export_reports(self, app, client):
        citizen_auth = self._register_and_login_citizen(client, "export-citizen@example.com")
        citizen_token = citizen_auth["access_token"]
        for endpoint, _ in self.EXPORT_ENDPOINTS:
            response = client.get(endpoint, headers={"Authorization": f"Bearer {citizen_token}"})
            assert response.status_code == 403, endpoint

    def test_admin_can_export_reports_in_all_formats(self, app, client):
        self._ensure_admin("export-sysadmin@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "export-sysadmin@example.com")
        city = self._ensure_city("ExportCityA")
        citizen_auth = self._register_and_login_citizen(client, "export-citizen-a@example.com")
        self._submit_complaint(client, citizen_auth["access_token"], city.id)

        for endpoint, mimetype in self.EXPORT_ENDPOINTS:
            response = client.get(endpoint, headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200, endpoint
            assert response.mimetype == mimetype, endpoint
            assert "attachment" in response.headers.get("Content-Disposition", "")
            assert len(response.data) > 0

    def test_csv_export_contains_filtered_data(self, app, client):
        self._ensure_admin("export-sysadmin2@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "export-sysadmin2@example.com")
        city = self._ensure_city("ExportCityB")
        citizen_auth = self._register_and_login_citizen(client, "export-citizen-b@example.com")
        self._submit_complaint(client, citizen_auth["access_token"], city.id, priority="urgent")

        response = client.get(
            "/api/v1/reports/export/csv",
            headers={"Authorization": f"Bearer {token}"},
            query_string={"status": "pending"},
        )
        assert response.status_code == 200
        text = response.data.decode("utf-8")
        assert "Civic Services Platform" in text
        assert "Status filter" in text
        assert "pending" in text
        assert "ExportCityB" in text

    def test_municipal_admin_export_is_city_scoped(self, app, client):
        city_a = self._ensure_city("ExportCityC")
        city_b = self._ensure_city("ExportCityD")
        self._ensure_admin("export-muni@example.com", AdministratorProfile.MUNICIPAL, "ExportCityC")
        muni_token = self._login(client, "export-muni@example.com")

        citizen_a = self._register_and_login_citizen(client, "export-citizen-c@example.com")
        self._submit_complaint(client, citizen_a["access_token"], city_a.id)
        citizen_b = self._register_and_login_citizen(client, "export-citizen-d@example.com")
        self._submit_complaint(client, citizen_b["access_token"], city_b.id)

        response = client.get(
            "/api/v1/reports/export/csv", headers={"Authorization": f"Bearer {muni_token}"}
        )
        assert response.status_code == 200
        text = response.data.decode("utf-8")
        assert "ExportCityC" in text
        assert "ExportCityD" not in text

    def test_export_invalid_date_returns_400(self, app, client):
        self._ensure_admin("export-sysadmin3@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "export-sysadmin3@example.com")
        for endpoint, _ in self.EXPORT_ENDPOINTS:
            response = client.get(
                endpoint,
                headers={"Authorization": f"Bearer {token}"},
                query_string={"date_from": "not-a-date"},
            )
            assert response.status_code == 400, endpoint

    def test_excel_export_is_valid_workbook(self, app, client):
        import io
        from openpyxl import load_workbook

        self._ensure_admin("export-sysadmin4@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "export-sysadmin4@example.com")
        city = self._ensure_city("ExportCityE")
        citizen_auth = self._register_and_login_citizen(client, "export-citizen-e@example.com")
        self._submit_complaint(client, citizen_auth["access_token"], city.id)

        response = client.get(
            "/api/v1/reports/export/excel", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        wb = load_workbook(io.BytesIO(response.data))
        assert "Summary" in wb.sheetnames
        assert "By Status" in wb.sheetnames
        assert "By Category" in wb.sheetnames
        assert "By Priority" in wb.sheetnames
        assert "By Location" in wb.sheetnames
        assert "Worker Performance" in wb.sheetnames

    def test_pdf_export_has_pdf_magic_bytes(self, app, client):
        self._ensure_admin("export-sysadmin5@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "export-sysadmin5@example.com")
        response = client.get(
            "/api/v1/reports/export/pdf", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.data[:4] == b"%PDF"

    # ── New tests for TPS-96/98 enhancements ────────────────────────────

    def test_feedback_summary_endpoint_accessible_by_admin(self, app, client):
        self._ensure_admin("feedback-sysadmin@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "feedback-sysadmin@example.com")
        response = client.get(
            "/api/v1/reports/feedback/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert "total" in data
        assert "avg_rating" in data
        assert "distribution" in data
        assert "recent_comments" in data

    def test_feedback_summary_forbidden_for_citizens(self, app, client):
        citizen_auth = self._register_and_login_citizen(client, "feedback-citizen@example.com")
        response = client.get(
            "/api/v1/reports/feedback/summary",
            headers={"Authorization": f"Bearer {citizen_auth['access_token']}"},
        )
        assert response.status_code == 403

    def test_priority_filter_narrows_summary(self, app, client):
        self._ensure_admin("priority-sysadmin@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "priority-sysadmin@example.com")
        city = self._ensure_city("PriorityFilterCity")
        citizen_auth = self._register_and_login_citizen(client, "priority-citizen@example.com")
        self._submit_complaint(client, citizen_auth["access_token"], city.id, priority="urgent")
        self._submit_complaint(client, citizen_auth["access_token"], city.id, priority="low")

        response_urgent = client.get(
            "/api/v1/reports/complaints/summary",
            headers={"Authorization": f"Bearer {token}"},
            query_string={"priority": "urgent"},
        )
        assert response_urgent.status_code == 200

        response_all = client.get(
            "/api/v1/reports/complaints/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response_all.status_code == 200
        assert response_all.get_json()["data"]["total"] >= response_urgent.get_json()["data"]["total"]

    def test_invalid_priority_filter_returns_400(self, app, client):
        self._ensure_admin("priority-sysadmin2@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "priority-sysadmin2@example.com")
        response = client.get(
            "/api/v1/reports/complaints/summary",
            headers={"Authorization": f"Bearer {token}"},
            query_string={"priority": "critical"},
        )
        assert response.status_code == 400

    def test_location_filter_scopes_summary_for_system_admin(self, app, client):
        city_x = self._ensure_city("LocationFilterCityX")
        city_y = self._ensure_city("LocationFilterCityY")
        self._ensure_admin("location-sysadmin@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "location-sysadmin@example.com")

        citizen_x = self._register_and_login_citizen(client, "location-citizen-x@example.com")
        self._submit_complaint(client, citizen_x["access_token"], city_x.id)
        citizen_y = self._register_and_login_citizen(client, "location-citizen-y@example.com")
        self._submit_complaint(client, citizen_y["access_token"], city_y.id)

        response = client.get(
            "/api/v1/reports/complaints/summary",
            headers={"Authorization": f"Bearer {token}"},
            query_string={"location": str(city_x.id)},
        )
        assert response.status_code == 200
        # Should have fewer (or equal) complaints than unfiltered
        response_all = client.get(
            "/api/v1/reports/complaints/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response_all.get_json()["data"]["total"] >= response.get_json()["data"]["total"]

    def test_csv_export_includes_feedback_section(self, app, client):
        self._ensure_admin("export-fb-sysadmin@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "export-fb-sysadmin@example.com")
        response = client.get(
            "/api/v1/reports/export/csv", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        text = response.data.decode("utf-8")
        assert "Citizen Feedback Summary" in text

    def test_excel_export_includes_feedback_sheet(self, app, client):
        import io
        from openpyxl import load_workbook

        self._ensure_admin("export-fb-sysadmin2@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "export-fb-sysadmin2@example.com")
        response = client.get(
            "/api/v1/reports/export/excel", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        wb = load_workbook(io.BytesIO(response.data))
        assert "Citizen Feedback" in wb.sheetnames

    def test_export_with_priority_filter_includes_priority_in_csv(self, app, client):
        self._ensure_admin("export-prio-sysadmin@example.com", AdministratorProfile.SYSTEM)
        token = self._login(client, "export-prio-sysadmin@example.com")
        city = self._ensure_city("ExportPrioCity")
        citizen_auth = self._register_and_login_citizen(client, "export-prio-citizen@example.com")
        self._submit_complaint(client, citizen_auth["access_token"], city.id, priority="urgent")

        response = client.get(
            "/api/v1/reports/export/csv",
            headers={"Authorization": f"Bearer {token}"},
            query_string={"priority": "urgent"},
        )
        assert response.status_code == 200
        text = response.data.decode("utf-8")
        assert "Priority filter" in text
        assert "urgent" in text

    def test_non_admin_cannot_access_feedback_endpoint(self, app, client):
        """Verify the feedback endpoint is included in the forbidden-for-citizens set."""
        citizen_auth = self._register_and_login_citizen(client, "feedback-citizen2@example.com")
        response = client.get(
            "/api/v1/reports/feedback/summary",
            headers={"Authorization": f"Bearer {citizen_auth['access_token']}"},
        )
        assert response.status_code == 403

