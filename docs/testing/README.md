# Testing Documentation

> Last reviewed: 2026-08-08

This folder contains test plans, test cases, and testing reports for the Civic Services Platform.

## Test Strategy

| Layer | Tool | Scope |
|---|---|---|
| Unit Tests | Pytest | Models, services, utilities |
| Integration Tests | Pytest + Flask test client | API endpoints |
| API Tests | Postman | End-to-end API flows |
| Frontend Tests | Vitest (future) | Vue components |

## Running Tests

### Backend

```bash
cd backend

# All tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=app --cov-report=html

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v
```

### Coverage Target

Minimum acceptable coverage: **80%**

## Admin Hierarchy Coverage

Current automated coverage for Municipal Administrator registration includes:
- successful System Administrator registration of a Municipal Administrator
- duplicate email conflict handling
- anonymous and citizen access denial
- password, confirm-password, and phone validation failures
- Municipal Administrator login with `admin_level` and `city_name`
- service-level audit-log creation for municipal-administrator registration

## Password Reset & Email Update Coverage (Milestone 4)

`tests/unit/test_admin_service.py` and `tests/integration/test_admin_hierarchy_api.py`
cover the administrator-driven password reset/email update capability added
this sprint:
- password reset (and subsequent login with the new password) for a Citizen,
  a Field Worker, and a Municipal Administrator
- email update, including a duplicate-email conflict returning `409`
- mismatched `confirm_password` returning `422`
- `/admin/users` correctly scoped to a Municipal Administrator's own city
  (citizens outside the city return `404`, not visible in the list)
- see `docs/milestone4/TEST_CASE_DOCUMENTATION.md` for the full
  `[Input | Expected | Actual | Result]` boxes, including one case where a
  new unit test caught a real case-sensitivity bug in the email-uniqueness
  check before it shipped

## Timezone (`UTCDateTime`) Regression Coverage

`tests/unit/test_models.py::TestUTCDateTime` locks in the fix for a bug where
datetimes were returned without a UTC offset (causing the frontend to
misparse them as local time, a 5:30h/IST display drift). Verifies both a
`User.created_at` and a `ComplaintAssignment.expected_completion_at` round-trip
as timezone-aware UTC after being reloaded from the database.

## Duplicate Pothole Detection Coverage

47 tests across `tests/integration/test_duplicate_detection_api.py` (13),
`tests/unit/test_duplicate_detection_service.py` (8),
`tests/unit/test_geo.py` (7, haversine-distance math), plus additions inside
`test_admin_service.py`, `test_citizen_service.py`, and `test_schemas.py`
(`TestMarkDuplicateSchema`). Covers: nearby-open-complaint lookup and city
scoping, marking a complaint as a duplicate (including self-reference and
already-a-duplicate rejection), citizen notification wording, the citizen
advisory nearby-duplicates check (missing/invalid coordinates → 400), and
updating the configurable `duplicate_detection_radius_meters` system
setting. This feature was reintegrated into the codebase in Milestone 4
after being found missing — see `docs/milestone4/USER_FEEDBACK_AND_NEXT_SPRINT.md`.

## Field Worker Coverage

`tests/integration/test_fieldworker_api.py` covers:
- auth-required checks on assignments list and dashboard
- full lifecycle: accept → in_progress → evidence photo upload → complete
- reject transitions the complaint back to `pending`
- ownership enforcement (a worker cannot view another worker's assignment — 404)
- dashboard summary counts by status

## Administrator City Scoping Coverage

`tests/integration/test_admin_city_scoping_api.py` covers:
- municipal administrators only see/can act on their own city's complaints (list, detail, assign)
- system administrators remain unscoped across all cities
- municipal administrators can create, list, view, edit, and activate/deactivate field workers in their own city only
- system administrators are forbidden (403) from creating field workers
- assigning a complaint to a field worker from a different city is rejected
- municipal dashboard summary reflects only that city's complaint/field-worker data

## Admin Complaint Workflow + Notifications Coverage

`tests/integration/test_admin_complaint_workflow_api.py` covers:
- priority can be changed independently of status
- invalid status jumps (e.g. pending → resolved, pending → closed) are rejected with 400
- full lifecycle: assign → accept → resolve → close, asserting a notification fires at each step
- rejecting a complaint notifies the citizen

## System Settings Coverage

`tests/integration/test_system_settings_api.py` covers:
- non-system-admins get 403 on both GET and PUT
- default settings are returned/created lazily
- updates persist and write an audit-log entry
- invalid `default_complaint_priority` / `support_email` are rejected
- `maintenance_mode` blocks non-administrator logins but not administrator logins
- `notify_on_status_change=false` suppresses notification creation for a status change

## Test File Naming

| Type | Pattern |
|---|---|
| Unit test | `test_<module>.py` |
| Integration test | `test_<endpoint>_api.py` |

## Testing Docs Backlog

- [ ] Add test plan document
- [ ] Add test case matrix
- [ ] Document Postman test runs
