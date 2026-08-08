# Sprint 3 Deliverables Status Report
## Milestone 4 — Due: 12 August 2026

**Project:** Civic Services Platform — Pothole Reporting and Resolution System
**Date:** 2026-08-08
**Status:** ✅ COMPLETE

---

## 📊 CURRENT STATUS OVERVIEW

### Test Coverage
| Item | Status | Details |
|---|---|---|
| **Total Test Cases** | ✅ 438 | All passing (was 182 at Milestone 3) |
| **New tests this milestone** | ✅ 19 written + 47 reintegrated | Written: 11 unit (`test_admin_service.py`) + 2 unit (`test_models.py`) + 6 integration (`test_admin_hierarchy_api.py`). Reintegrated: `test_duplicate_detection_api.py` (13), `test_duplicate_detection_service.py` (8), `test_geo.py` (7), plus additions inside `test_admin_service.py`/`test_citizen_service.py`/`test_schemas.py` |
| **Test Pass Rate** | ✅ 100% | 438 passed in ~60s |
| **flake8** | ✅ Clean | `flake8 app/ --max-line-length=120` — 0 violations |

### API Documentation
| Item | Status | Details |
|---|---|---|
| **Updated YAML** | ✅ Done | `openapi-with-user-stories.yaml` — 60 paths / 69 operations, re-validated with `openapi-spec-validator` |
| **Updated api_mapping.json** | ✅ Done | New feedback-summary endpoint + 3 updated endpoints + 3 reintegrated duplicate-detection endpoints reflected |
| **Diff against live routes** | ✅ Done | Full `app.url_map` diff performed; found exactly 1 undocumented endpoint (`GET /reports/feedback/summary`), now added |
| **Error Handling** | ✅ Complete | 409 (duplicate email), 422 (weak password / confirm mismatch), 404 (city-scoping), 400 (duplicate-detection business rules) all documented per changed/new endpoint |
| **User Story Mapping** | ✅ Done | Changed endpoints mapped to TPS-27/TPS-33/TPS-96/TPS-98, or explicitly flagged "added beyond baseline" |

### Test Case Format
| Item | Status | Details |
|---|---|---|
| **Required Format** | ✅ Done | `[API being tested \| Inputs \| Expected Output \| Actual Output \| Result]` used throughout `TEST_CASE_DOCUMENTATION.md` |
| **Actual vs Expected divergence example** | ✅ Done | Featured case: duplicate-email case-sensitivity bug found by a new unit test, fixed, re-verified |

---

## 📋 DELIVERABLE CHECKLIST (per `PROJECT DETAILS MAY 2026.pdf`)

### 1. ✅ Changes made based on user feedback — COMPLETE
- 6 real, reproduced user-reported issues fixed this sprint, each with root
  cause and resolution documented in `USER_FEEDBACK_AND_NEXT_SPRINT.md`:
  timezone display bug, rejected-complaint UI still editable, missing
  password-reset capability, citizen/city-scoping gaps in admin management,
  the Reports page's `hasReportData` bug, and a fully-built duplicate-pothole-
  detection feature that had gone missing due to an abandoned branch merge
  (traced via `git log` and reintegrated via `git cherry-pick`).

### 2. ✅ Updated documentation of APIs in a Swagger-compatible YAML file — COMPLETE
- `openapi-with-user-stories.yaml`, validated as genuine OpenAPI 3.0
  (`openapi-spec-validator`), with error handling, User Story mapping, and a
  description of every changed/new endpoint.

### 3. ✅ Backend code of the implemented APIs — COMPLETE
- `backend/app/api/administrator/service.py` / `controller.py`,
  `backend/app/schemas/user_schema.py`, `backend/app/utils/db_types.py`,
  and 12 model files — all committed, tested, flake8-clean.

### 4. ✅ Proper test cases to test the updated APIs — COMPLETE
- `TEST_CASE_DOCUMENTATION.md`, 19 newly-written + 47 reintegrated cases in
  the required format, each with real input/expected/actual values sourced
  from actual pytest runs.

### 5. ✅ Submit pytest code for the updated APIs — COMPLETE
- All 19 new tests are real, committed pytest code in
  `backend/tests/unit/test_admin_service.py`,
  `backend/tests/unit/test_models.py`, and
  `backend/tests/integration/test_admin_hierarchy_api.py`. The 47
  reintegrated duplicate-detection tests live in
  `backend/tests/integration/test_duplicate_detection_api.py`,
  `backend/tests/unit/test_duplicate_detection_service.py`, and
  `backend/tests/unit/test_geo.py`.
- Raw output: `pytest_full_output.txt`. Formatted report:
  `PYTEST_RESULTS_REPORT.md`.

### 6. ✅ Extra user stories for work beyond the Jira baseline — COMPLETE
- `Jira.csv` in this folder is a copy of `docs/project-guide/Jira.csv` with
  additional rows appended (`TPS-ADD-*`) for every feature implemented
  beyond the original 55-story baseline: the Administrator Hierarchy
  (System/Municipal Admin split), Cities/Pincodes + public Locations API,
  mandatory photo-first pothole reporting with map pin, the
  administrator-driven password-reset/email-update capability delivered
  this sprint, and duplicate pothole detection (reintegrated this sprint).

---

## 🔧 TECHNICAL DETAILS

### Files Changed This Sprint (backend)
```
backend/app/api/administrator/controller.py    (decorators, swagger models, error mapping, duplicate-detection routes)
backend/app/api/administrator/service.py       (password/email logic, city scoping, bug fix, duplicate-detection methods)
backend/app/api/citizen/controller.py          (nearby-duplicates route)
backend/app/api/citizen/service.py             (check_nearby_duplicates)
backend/app/schemas/user_schema.py             (email/password fields on 3 update schemas)
backend/app/schemas/complaint_schema.py        (MarkDuplicateSchema)
backend/app/schemas/system_setting_schema.py   (duplicate_detection_radius_meters)
backend/app/utils/db_types.py                  (NEW — UTCDateTime type)
backend/app/utils/geo.py                       (NEW — haversine distance helper, reintegrated)
backend/app/utils/api_fields.py                (NEW — NullableString, reintegrated)
backend/app/services/duplicate_detection_service.py  (NEW, reintegrated)
backend/app/services/system_settings_service.py      (duplicate_detection_radius_meters)
backend/app/models/*.py (12 files)             (DateTime -> UTCDateTime)
backend/app/models/complaint.py                (duplicate_of_id, duplicate_reason columns, reintegrated)
backend/app/models/system_setting.py           (duplicate_detection_radius_meters column)
backend/migrations/versions/a1b2c3d4e5f6_add_duplicate_complaint_detection.py  (reintegrated, rebased onto a single migration head)
backend/tests/unit/test_admin_service.py       (+11 password/email tests, plus reintegrated duplicate-detection unit tests)
backend/tests/unit/test_models.py              (+2 tests, new TestUTCDateTime class)
backend/tests/integration/test_admin_hierarchy_api.py  (+6 tests, 1 rewritten)
backend/tests/integration/test_duplicate_detection_api.py    (NEW, 13 tests, reintegrated)
backend/tests/unit/test_duplicate_detection_service.py       (NEW, 8 tests, reintegrated)
backend/tests/unit/test_geo.py                                (NEW, 7 tests, reintegrated)
```

### Files Changed This Sprint (frontend)
```
frontend/src/pages/administrator/Citizens.vue               (NEW page)
frontend/src/pages/administrator/MunicipalAdministrators.vue (Edit Details + Reset Password split)
frontend/src/pages/administrator/FieldWorkers.vue             (Edit Details + Reset Password split)
frontend/src/pages/administrator/AdminComplaintDetails.vue    (terminal-status Priority gating fix, duplicate-review panel reintegrated)
frontend/src/pages/administrator/AdministratorDashboard.vue   (duplicate badge, reintegrated)
frontend/src/pages/administrator/SystemSettings.vue           (duplicate_detection_radius_meters field, plus a settings-load bug fixed during verification)
frontend/src/pages/citizen/ReportComplaint.vue                (possible-duplicate warning, reintegrated)
frontend/src/pages/citizen/ComplaintDetails.vue, TrackComplaint.vue  (duplicate status display, reintegrated)
frontend/src/pages/administrator/Reports.vue                  (hasReportData bug fix)
frontend/src/services/admin.service.js, complaint.service.js  (new API client methods)
frontend/src/router/index.js, src/components/Sidebar.vue      (Citizens route/nav)
```

---

## ✅ ALL ACTION ITEMS RESOLVED

| Item | Status |
|---|---|
| Fix timezone display bug | ✅ Done — `UTCDateTime`, 2 regression tests |
| Fix rejected-complaint UI still editable | ✅ Done — `isTerminalStatus` gating |
| Add password-reset capability (3 roles) | ✅ Done — 3 endpoints extended, 11 unit + 6 integration tests |
| Open `/admin/users` to municipal admins (city-scoped) | ✅ Done — 2 tests |
| Add email-update capability alongside password reset | ✅ Done |
| Split "Edit Details" and "Reset Password" into separate UI actions | ✅ Done — `Citizens.vue`, `MunicipalAdministrators.vue`, `FieldWorkers.vue` |
| Fix Reports page `hasReportData` bug | ✅ Done |
| Update `openapi-with-user-stories.yaml` / `api_mapping.json` | ✅ Done |
| Create test documentation | ✅ Done — `TEST_CASE_DOCUMENTATION.md` |
| Create pytest report + raw output | ✅ Done |
| User feedback + next sprint plan | ✅ Done |
| Copy `Jira.csv` + document beyond-baseline stories | ✅ Done |
| Reintegrate the duplicate-detection feature (missing due to abandoned branch merge) | ✅ Done — `git cherry-pick`, migration head rebase, 47 tests, settings-load bug fixed |

**Status**: ✅ ALL SPRINT 3 / MILESTONE 4 DELIVERABLES COMPLETE
