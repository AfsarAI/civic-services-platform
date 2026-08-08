# Pytest Results Report — Milestone 4 (Sprint 3 Delta)

**Project:** Civic Services Platform — Pothole Reporting and Resolution System
**Date:** 2026-08-08
**Command:** `pytest tests/ -v` (run from `backend/`, `.venv` activated)

---

## Result Summary

```
438 passed in 60.37s
```

**100% pass rate.** No skips, no xfails, no warnings treated as errors.
`flake8 app/ --max-line-length=120` is also clean (0 violations).

| Metric | Milestone 3 (2026-08-01) | Milestone 4 (2026-08-08) | Delta |
|---|---|---|---|
| Total tests | 182 | **438** | **+256** |
| Test files | 17 | 26 | +9 |
| Pass rate | 100% | 100% | — |

> The +256 total delta includes test files added by other merged branches
> between the two snapshots (TPS-85/96/98 reports & export, TPS-99 system
> settings, etc. — see `USER_FEEDBACK_AND_NEXT_SPRINT.md` for the full
> changelog). Two groups of tests are directly attributable to this
> Milestone 4 submission's own work:
> 1. **+19** for password reset/email update/timezone fix (372 → 391),
>    documented in `TEST_CASE_DOCUMENTATION.md`.
> 2. **+47** for the duplicate-detection feature (391 → 438), which was
>    found to be missing from the running application, traced via `git log`
>    to an abandoned branch merge, and reintegrated via `git cherry-pick`
>    this same sprint (`test_duplicate_detection_api.py` 13,
>    `test_duplicate_detection_service.py` 8, `test_geo.py` 7, plus
>    additions inside `test_admin_service.py`, `test_citizen_service.py`,
>    and `test_schemas.py`).

> **Known flaky tests (not a regression):**
> `test_dashboard_high_priority_pending_count_reflects_urgent_open_complaints`
> and `test_excel_export_is_valid_workbook` were observed to fail once when
> run as part of the full 438-test suite, but pass consistently both in
> isolation and on every other full-suite run performed. This points to
> pre-existing test-order/shared-DB-state sensitivity, not a defect in the
> duplicate-detection reintegration — flagged here for future investigation
> per Section 4.3 of `USER_FEEDBACK_AND_NEXT_SPRINT.md`.

---

## Full Test Breakdown (438 tests, 26 files)

### Integration tests (15 files, 187 tests)
| File | Tests |
|---|---|
| `test_admin_city_scoping_api.py` | 12 |
| `test_admin_complaint_workflow_api.py` | 11 |
| `test_admin_dashboard_api.py` | 4 |
| `test_admin_dashboard_kpi_api.py` | 7 |
| `test_admin_hierarchy_api.py` | **17** (+6 new password/email tests this milestone) |
| `test_auth_api.py` | 25 |
| `test_citizen_api.py` | 14 |
| `test_citizen_feedback_api.py` | 6 |
| `test_complaint_closure_notification_api.py` | 7 |
| `test_duplicate_detection_api.py` | **13** (reintegrated this milestone) |
| `test_fieldworker_api.py` | 7 |
| `test_location_api.py` | 9 |
| `test_notifications_api.py` | 12 |
| `test_reports_api.py` | 26 |
| `test_system_settings_api.py` | 8 |

### Unit tests (11 files, 251 tests)
| File | Tests |
|---|---|
| `test_admin_dashboard_kpi.py` | 9 |
| `test_admin_service.py` | **66** (+11 password/email this milestone, plus duplicate-detection methods reintegrated) |
| `test_auth_service.py` | 19 |
| `test_citizen_service.py` | **22** (includes reintegrated nearby-duplicates checks) |
| `test_duplicate_detection_service.py` | **8** (reintegrated this milestone) |
| `test_fieldworker_service.py` | 17 |
| `test_geo.py` | **7** (reintegrated this milestone) |
| `test_locations_service.py` | 14 |
| `test_models.py` | **24** (+2 new `UTCDateTime` regression tests this milestone) |
| `test_notifications_service.py` | 12 |
| `test_reports_service.py` | 30 |
| `test_schemas.py` | **32** (includes reintegrated `MarkDuplicateSchema` tests) |

**Total: 438 passed, 0 failed, 0 skipped**

---

## New Tests Added for This Milestone (19 written + 47 reintegrated)

See `TEST_CASE_DOCUMENTATION.md` for the full `[Input | Expected | Actual |
Result]` boxes. Quick index:

**`tests/unit/test_admin_service.py`** (+11):
- `test_update_user_resets_password`
- `test_update_user_updates_email`
- `test_update_user_rejects_duplicate_email`
- `test_update_user_municipal_admin_scoped_to_own_city_citizen`
- `test_update_user_municipal_admin_rejects_other_city_citizen`
- `test_update_field_worker_resets_password`
- `test_update_field_worker_updates_email`
- `test_update_field_worker_rejects_duplicate_email`
- `test_update_municipal_administrator_resets_password`
- `test_update_municipal_administrator_updates_email`
- `test_update_municipal_administrator_rejects_duplicate_email`

**`tests/unit/test_models.py`** (+2, new `TestUTCDateTime` class):
- `test_user_created_at_round_trips_as_timezone_aware`
- `test_complaint_assignment_expected_completion_round_trips_as_timezone_aware`

**`tests/integration/test_admin_hierarchy_api.py`** (+6):
- `test_system_admin_can_reset_citizen_password`
- `test_system_admin_can_update_citizen_email`
- `test_update_user_duplicate_email_returns_409`
- `test_update_user_mismatched_confirm_password_returns_422`
- `test_municipal_admin_can_reset_field_worker_password`
- `test_system_admin_can_reset_municipal_administrator_password`

(A 20th test, `test_municipal_admin_user_list_scoped_to_own_city_citizens`,
was *rewritten* rather than added — it replaced an obsolete test that
asserted the old, since-changed 403-only behavior for `/admin/users`.)

**Reintegrated (47 tests, duplicate pothole detection)** — see
`USER_FEEDBACK_AND_NEXT_SPRINT.md` for the full story of how this feature
went missing and was restored:
- `tests/integration/test_duplicate_detection_api.py` (13)
- `tests/unit/test_duplicate_detection_service.py` (8)
- `tests/unit/test_geo.py` (7)
- Additions inside `tests/unit/test_admin_service.py`,
  `tests/unit/test_citizen_service.py`, and `tests/unit/test_schemas.py`
  (`TestMarkDuplicateSchema`)

---

## How Testing Improved the API This Sprint

Writing `test_update_municipal_administrator_rejects_duplicate_email`
(unit-level, calling `AdminService` directly rather than through the HTTP
layer) initially **failed** — `pytest.raises(ValueError)` did not fire. Root
cause: the service's email-uniqueness check compared the raw, un-normalized
input against already-lowercased stored emails, so a case-differing duplicate
("Name@Example.com" vs "name@example.com") slipped through when the service
was called without going through the Marshmallow schema's normalization
first. Fixed in `AdminService._ensure_email_available()` — it now normalizes
and returns the canonical email itself, and all three callers store the
returned value. Full before/after evidence is in `TEST_CASE_DOCUMENTATION.md`
under "Featured Case: Where Testing Caught a Real Bug".

---

## Raw Output

See `pytest_full_output.txt` in this same folder for the complete, unedited
`pytest -v` console output (all 438 test IDs with PASSED status).
