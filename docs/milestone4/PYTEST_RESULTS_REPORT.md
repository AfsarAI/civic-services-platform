# Pytest Results Report — Milestone 4 (Sprint 3 Delta)

**Project:** Civic Services Platform — Pothole Reporting and Resolution System
**Date:** 2026-08-08
**Command:** `pytest tests/ -v` (run from `backend/`, `.venv` activated)

---

## Result Summary

```
391 passed in 56.14s
```

**100% pass rate.** No skips, no xfails, no warnings treated as errors.
`flake8 app/ --max-line-length=120` is also clean (0 violations).

| Metric | Milestone 3 (2026-08-01) | Milestone 4 (2026-08-08) | Delta |
|---|---|---|---|
| Total tests | 182 | **391** | **+209** |
| Test files | 17 | 23 | +6 |
| Pass rate | 100% | 100% | — |

> The +209 total delta includes test files added by other merged branches
> between the two snapshots (TPS-85/96/98 reports & export, TPS-99 system
> settings, etc. — see `USER_FEEDBACK_AND_NEXT_SPRINT.md` for the full
> changelog). The tests written **specifically for this Milestone 4
> submission's API changes** (password reset, email update, city-scoped
> `/admin/users`, timezone fix) are the **+19** documented in
> `TEST_CASE_DOCUMENTATION.md`, going from 372 → 391.

---

## Full Test Breakdown (391 tests, 23 files)

### Integration tests (14 files, 174 tests)
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
| `test_fieldworker_api.py` | 7 |
| `test_location_api.py` | 9 |
| `test_notifications_api.py` | 12 |
| `test_reports_api.py` | 26 |
| `test_system_settings_api.py` | 8 |

### Unit tests (9 files, 217 tests)
| File | Tests |
|---|---|
| `test_admin_dashboard_kpi.py` | 9 |
| `test_admin_service.py` | **56** (+11 new password/email tests this milestone) |
| `test_auth_service.py` | 19 |
| `test_citizen_service.py` | 19 |
| `test_fieldworker_service.py` | 17 |
| `test_locations_service.py` | 14 |
| `test_models.py` | **24** (+2 new `UTCDateTime` regression tests this milestone) |
| `test_notifications_service.py` | 12 |
| `test_reports_service.py` | 30 |
| `test_schemas.py` | 26 |

**Total: 391 passed, 0 failed, 0 skipped**

---

## New Tests Added for This Milestone (19 total)

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
`pytest -v` console output (all 391 test IDs with PASSED status).
