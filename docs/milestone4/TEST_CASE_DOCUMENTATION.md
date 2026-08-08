# Test Case Documentation — Milestone 4 (Sprint 3 Delta)

**Project:** Civic Services Platform — Pothole Reporting and Resolution System
**Scope:** Test cases for the **updated/new APIs** delivered since Milestone 3
(2026-08-01): administrator-driven password reset & email update on 3
endpoints, the city-scoped `/admin/users` access for municipal administrators,
the newly-documented `/reports/feedback/summary` endpoint, and the
`UTCDateTime` timezone fix.

Format (as required):
```
[ API being tested, Inputs, Expected output, Actual Output, Result - Success/Fail ]
```

All boxes below are sourced directly from real pytest runs (see
`PYTEST_RESULTS_REPORT.md` and `pytest_full_output.txt` in this same folder) —
no values are fabricated.

---

## ⭐ Featured Case: Where Testing Caught a Real Bug (Actual ≠ Expected)

This is the case the milestone rubric specifically calls out — a test whose
**first run's actual output differed from the expected output**, which
directly led to a source-code fix.

```
API being tested: PUT /api/v1/admin/municipal-administrators/{id}
                  (AdminService.update_municipal_administrator, unit-level)
Test case: test_update_municipal_administrator_rejects_duplicate_email
Inputs:
  - Administrator A created with email "debug.muni.dupa@example.com"
  - Administrator B created with email "debug.muni.dupb@example.com"
  - Update Administrator A: { "email": "debug.muni.dupB@example.com" }
    (same address as B, but with a capital "B")
Expected Output:
  - ValueError("An account with this email already exists.") is raised
  - HTTP 409 when exercised through the real endpoint
Actual Output (BEFORE fix):
  - No exception raised — the update succeeded and Administrator A's email
    was silently changed to a duplicate (differing only by case) of
    Administrator B's email.
  - Root cause: `_ensure_email_available()` queried `User.query.filter_by(
    email=email)` using the raw, un-normalized input. SQLite string
    comparison is case-sensitive, so "debug.muni.dupB@example.com" (capital B)
    did not match the stored "debug.muni.dupb@example.com" (lowercase, from
    the original creation which *does* normalize). The Marshmallow schema
    normally lower-cases `email` before the service ever sees it, so this
    only manifested when the service method was exercised directly by this
    new unit test — a real defense-in-depth gap.
Result: FAIL (on first run) → Fixed → PASS
Fix applied: `AdminService._ensure_email_available()` now normalizes
  (`.strip().lower()`) the candidate email itself and returns the normalized
  value, and all three callers (`update_user`, `update_field_worker`,
  `update_municipal_administrator`) now assign the *returned* normalized
  value to `user.email` instead of the raw input — so the check and the
  stored value can never disagree, regardless of what the caller passes in.
Actual Output (AFTER fix): ValueError("An account with this email already
  exists.") raised, matching Expected Output exactly.
```

---

## 1. Password Reset — `PUT /api/v1/admin/users/{id}` (Citizens, System Admin)

```
API being tested: PUT /api/v1/admin/users/{id}
Test case: test_system_admin_can_reset_citizen_password (integration)
Inputs:
  - Logged in as System Administrator (sysadmin-pwreset@civicservices.local)
  - Citizen account exists with password "OldSecret@123"
  - Request: PUT /api/v1/admin/users/{citizen_id}
    Body: { "password": "NewSecret@123", "confirm_password": "NewSecret@123" }
Expected Output:
  - HTTP 200, { "success": true, ... }
  - A subsequent POST /api/v1/auth/login with the OLD password returns 401
  - A subsequent POST /api/v1/auth/login with the NEW password returns 200
Actual Output:
  - HTTP 200, { "success": true, ... }
  - Old-password login: HTTP 401
  - New-password login: HTTP 200
Result: Success
```

```
API being tested: PUT /api/v1/admin/users/{id}
Test case: test_update_user_mismatched_confirm_password_returns_422
Inputs:
  - Logged in as System Administrator
  - Request: PUT /api/v1/admin/users/{citizen_id}
    Body: { "password": "NewSecret@123", "confirm_password": "Different@123" }
Expected Output:
  - HTTP 422, errors.confirm_password present
Actual Output:
  - HTTP 422, { "success": false, "errors": { "confirm_password":
    ["Confirm password must match password."] } }
Result: Success
```

```
API being tested: PUT /api/v1/admin/users/{id}
Test case: test_update_user_duplicate_email_returns_409
Inputs:
  - Two citizens exist: dup-citizen-a@example.com, dup-citizen-b@example.com
  - Request: PUT /api/v1/admin/users/{citizen_a_id}
    Body: { "email": "dup-citizen-b@example.com" }
Expected Output:
  - HTTP 409, message contains "already exists"
Actual Output:
  - HTTP 409, { "success": false, "message": "An account with this email
    already exists." }
Result: Success
```

```
API being tested: PUT /api/v1/admin/users/{id}
Test case: test_system_admin_can_update_citizen_email
Inputs:
  - Logged in as System Administrator
  - Request: PUT /api/v1/admin/users/{citizen_id}
    Body: { "email": "citizen-emailupdate-new@example.com" }
Expected Output:
  - HTTP 200, data.user.email == "citizen-emailupdate-new@example.com"
Actual Output:
  - HTTP 200, data.user.email == "citizen-emailupdate-new@example.com"
Result: Success
```

## 2. Password Reset — `PUT /api/v1/admin/field-workers/{id}` (Municipal Admin)

```
API being tested: PUT /api/v1/admin/field-workers/{id}
Test case: test_municipal_admin_can_reset_field_worker_password (integration)
Inputs:
  - Logged in as Municipal Administrator (city: Kanpur)
  - Field worker exists in the same city with password "OldWorker@123"
  - Request: PUT /api/v1/admin/field-workers/{worker_id}
    Body: { "password": "NewWorker@123", "confirm_password": "NewWorker@123" }
Expected Output:
  - HTTP 200
  - POST /api/v1/auth/login with the NEW password returns 200
Actual Output:
  - HTTP 200
  - New-password login: HTTP 200
Result: Success
```

```
API being tested: AdminService.update_field_worker (unit)
Test case: test_update_field_worker_updates_email
Inputs:
  - Municipal admin, field worker in the same city
  - service.update_field_worker(worker.id, admin, {"email": "...new@example.com"})
Expected Output:
  - Returned user.email == "mgmt.fw.email.worker.new@example.com"
Actual Output:
  - Returned user.email == "mgmt.fw.email.worker.new@example.com"
Result: Success
```

```
API being tested: AdminService.update_field_worker (unit)
Test case: test_update_field_worker_rejects_duplicate_email
Inputs:
  - Two field workers in the same city: mgmt.fw.dupa@..., mgmt.fw.dupb@...
  - service.update_field_worker(worker_a.id, admin, {"email": "mgmt.fw.dupb@..."})
Expected Output:
  - ValueError("An account with this email already exists.")
Actual Output:
  - ValueError("An account with this email already exists.")
Result: Success
```

## 3. Password Reset — `PUT /api/v1/admin/municipal-administrators/{id}` (System Admin)

```
API being tested: PUT /api/v1/admin/municipal-administrators/{id}
Test case: test_system_admin_can_reset_municipal_administrator_password (integration)
Inputs:
  - Logged in as System Administrator
  - Municipal admin exists (city: Nagpur)
  - Request: PUT /api/v1/admin/municipal-administrators/{muni_id}
    Body: { "password": "NewMunicipal@123", "confirm_password": "NewMunicipal@123" }
Expected Output:
  - HTTP 200
  - POST /api/v1/auth/login with the NEW password returns 200
Actual Output:
  - HTTP 200
  - New-password login: HTTP 200
Result: Success
```

```
API being tested: AdminService.update_municipal_administrator (unit)
Test case: test_update_municipal_administrator_updates_email
Inputs:
  - System admin creates a municipal admin, then calls
    service.update_municipal_administrator(muni_id, sysadmin.id, {"email": "...new@example.com"})
Expected Output:
  - Returned user.email == "mgmt.hierarchy.muni.email.new@example.com"
Actual Output:
  - Returned user.email == "mgmt.hierarchy.muni.email.new@example.com"
Result: Success
```

## 4. City-Scoped `/admin/users` for Municipal Administrators

```
API being tested: GET /api/v1/admin/users
Test case: test_municipal_admin_user_list_scoped_to_own_city_citizens
Inputs:
  - Municipal Administrator logged in, city = Delhi
  - Citizen "delhi-citizen@example.com" exists in Delhi
  - Citizen "mumbai-citizen@example.com" exists in Mumbai (different city)
  - Request: GET /api/v1/admin/users (no query params — role filter should be
    forced server-side regardless)
Expected Output:
  - HTTP 200
  - "delhi-citizen@example.com" present in data.items
  - "mumbai-citizen@example.com" absent from data.items
  - Every returned item has role == "citizen" (field workers/other admins
    excluded even though the endpoint is not role-filtered by the caller)
Actual Output:
  - HTTP 200
  - "delhi-citizen@example.com" present, "mumbai-citizen@example.com" absent
  - All returned items have role == "citizen"
Result: Success
```

```
API being tested: AdminService.update_user (unit)
Test case: test_update_user_municipal_admin_rejects_other_city_citizen
Inputs:
  - Municipal admin (city A) calls service.update_user(citizen_in_city_B.id,
    admin.id, {"first_name": "Nope"}, acting_admin=admin)
Expected Output:
  - ValueError("User not found.") — a municipal admin cannot even detect the
    existence of a citizen outside their city (404, not 403, to avoid
    leaking existence, consistent with the rest of the city-scoping design)
Actual Output:
  - ValueError("User not found.")
Result: Success
```

## 5. Timezone Fix Regression Tests

```
API being tested: User model / UTCDateTime column type (unit)
Test case: test_user_created_at_round_trips_as_timezone_aware
Inputs:
  - Create a User, commit, expire the session, reload from the database
Expected Output:
  - reloaded.created_at.tzinfo is not None
  - reloaded.created_at.isoformat() ends with "+00:00"
Actual Output:
  - tzinfo == datetime.timezone.utc
  - isoformat() == "...T...+00:00"
Result: Success
```

```
API being tested: ComplaintAssignment.expected_completion_at / UTCDateTime (unit)
Test case: test_complaint_assignment_expected_completion_round_trips_as_timezone_aware
Inputs:
  - Store expected_completion_at = datetime(2026, 8, 1, 11, 30, 0, tzinfo=UTC)
  - Commit, expire session, reload
Expected Output:
  - reloaded.expected_completion_at.isoformat() == "2026-08-01T11:30:00+00:00"
Actual Output:
  - "2026-08-01T11:30:00+00:00"
Result: Success

Context: before the fix, this same reload produced the naive string
"2026-08-01T11:30:00" (no offset), which the frontend's `new Date(...)`
misparsed as local time — displaying 5:30 hours behind (IST) for any
field-worker "expected completion" timestamp, or any other datetime field
in the API. This test locks the fix in as a permanent regression guard.
```

## 6. `GET /api/v1/reports/feedback/summary` (documentation gap closed, not new code)

```
API being tested: GET /api/v1/reports/feedback/summary
Test case: test_feedback_summary_forbidden_for_citizens (existing,
           tests/integration/test_reports_api.py) — this endpoint already had
           pytest coverage before Milestone 4; the gap being closed here is
           that it was missing from the Milestone 3 openapi-with-user-stories.yaml.
Inputs: Logged in as a citizen (non-admin role), GET /api/v1/reports/feedback/summary
Expected Output: HTTP 403
Actual Output: HTTP 403
Result: Success
```

```
API being tested: GET /api/v1/reports/feedback/summary
Test case: test_feedback_summary_endpoint_accessible_by_admin (existing)
Inputs: Logged in as System Administrator, GET /api/v1/reports/feedback/summary
Expected Output: HTTP 200, data contains total/avg_rating/distribution/recent_comments
Actual Output: HTTP 200, all four keys present
Result: Success
```

---

## Summary

| Category | New/updated test cases | Result |
|---|---|---|
| Password reset (citizen, via `/admin/users/{id}`) | 4 | 4/4 Success |
| Password reset (field worker, via `/admin/field-workers/{id}`) | 3 | 3/3 Success |
| Password reset (municipal admin, via `/admin/municipal-administrators/{id}`) | 3 | 3/3 Success |
| City-scoped `/admin/users` for municipal admins | 2 | 2/2 Success |
| Timezone (`UTCDateTime`) regression | 2 | 2/2 Success |
| Real bug found & fixed (email case-sensitivity) | 1 | Fail → Fixed → Success |
| **Total new test cases this milestone** | **19** (11 unit + 2 unit-model + 6 integration) | **19/19 passing after the fix above** |

Full suite: **391/391 passing** (was 372 at Milestone 3; +19 net new tests).
See `PYTEST_RESULTS_REPORT.md` for the complete run and `pytest_full_output.txt`
for the raw verbose log of every one of the 391 tests.
