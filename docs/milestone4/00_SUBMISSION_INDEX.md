# 🎓 IITM LxT Sprint 3 Submission Package — Milestone 4
## Civic Services Platform – Pothole Reporting and Resolution System

**Course:** Software Engineering (LxT 7.6)
**Institution:** IITM Online BS Degree
**Team:** MAY2026-Team-005
**Submission Date:** 2026-08-08
**Deadline:** 12 August 2026

---

## 📋 QUICK START

### For Reviewers (Start Here)
1. **Read this file first** — you are here ✓
2. **Read `USER_FEEDBACK_AND_NEXT_SPRINT.md`** — every change in this
   milestone traces back to a specific, reproduced user-reported bug or a
   test-driven finding, documented there first.
3. **Review the updated API spec** → `openapi-with-user-stories.yaml`
   (validated OpenAPI 3.0, 60 paths / 69 operations — see its `info.
   x-changes-since-milestone-3` field for the exact delta)
4. **Review the new test cases** → `TEST_CASE_DOCUMENTATION.md`
5. **Verify pytest results** → `PYTEST_RESULTS_REPORT.md` + `pytest_full_output.txt`

### This Package Is a *Delta* on Top of Milestone 3
Milestone 3 (`docs/milestone3/`, submitted 2026-08-01) already documented all
56 baseline endpoints, 182 test cases, and the full architecture. This
Milestone 4 package does **not** duplicate that content — it documents
exactly what changed since then: 3 updated endpoints (password reset + email
update, capability added to `PUT /admin/users/{id}`, `/admin/field-workers/
{id}`, `/admin/municipal-administrators/{id}`), 1 previously-undocumented
endpoint (`GET /reports/feedback/summary`), a cross-cutting timezone bug fix,
a fully reintegrated duplicate-pothole-detection feature (3 more endpoints —
see below), and 19 newly written + 47 reintegrated automated tests. Where
something is unchanged since Milestone 3 (database schema, authentication
design, RBAC decorators, etc.) this package references the Milestone 3 files
rather than repeating them.

---

## 📦 SUBMISSION DELIVERABLES

| File | Purpose |
|---|---|
| **openapi-with-user-stories.yaml** | Updated OpenAPI 3.0 spec — 60 paths / 69 operations, validated with `openapi-spec-validator`. `info.x-changes-since-milestone-3` documents exactly what changed. |
| **api_mapping.json** | Machine-readable endpoint→story mapping, updated to match |
| **TEST_CASE_DOCUMENTATION.md** | 19 newly-written + 47 reintegrated test cases in the required `[API \| Input \| Expected \| Actual \| Result]` format, including one case where testing caught and fixed a real bug |
| **PYTEST_RESULTS_REPORT.md** | Full 438-test run breakdown, delta vs Milestone 3's 182 |
| **pytest_full_output.txt** | Raw `pytest -v` console output (all 438 test IDs) |
| **USER_FEEDBACK_AND_NEXT_SPRINT.md** | The 6 user-reported issues this sprint, root cause + fix for each, plus Sprint 4 plan |
| **SPRINT_3_DELIVERABLES_STATUS.md** | Checklist mapping this package to the PDF's required deliverables |
| **Jira.csv** | Copy of the baseline Jira export, `+` new rows for every feature implemented beyond the original 55-story baseline (see file for the added rows, tagged `TPS-ADD-*`) |

---

## 🎯 Rubric Coverage (Sprint 1/2/3 template, per `PROJECT DETAILS MAY 2026.pdf`)

### API Creation and Integration
- Updated YAML lists all 3 changed endpoints, the 1 newly-documented
  endpoint, and the 3 reintegrated duplicate-detection endpoints, each with a
  `description` explaining exactly what's new, mapped to Jira story
  TPS-96/TPS-27/TPS-33/TPS-98 (or explicitly flagged "added beyond baseline"
  where no TPS story exists) — see the `info.x-changes-since-milestone-3`
  block and the updated "Summary of Related Jira Stories" appendix at the end
  of the YAML.

### Code for the APIs — Implementation
- Real backend code changes: `backend/app/api/administrator/service.py`,
  `backend/app/api/administrator/controller.py`,
  `backend/app/schemas/user_schema.py` (password/email fields + validation),
  `backend/app/utils/db_types.py` (new `UTCDateTime` type),
  12 model files (timezone fix).
- All changes are error-handled (409 email conflict, 422 validation, 404
  city-scoping) and covered by tests.

### Test Case Design & pytest
- 19 newly-written + 47 reintegrated test cases, both unit (`AdminService`
  called directly) and integration (full HTTP request/response through
  Flask's test client), documented in the required box format in
  `TEST_CASE_DOCUMENTATION.md`.
- Includes a genuine actual≠expected case (duplicate-email case-sensitivity
  bug) demonstrating testing improving the API, exactly as the rubric
  requests.
- 438/438 tests passing, raw output in `pytest_full_output.txt`.

### User Feedback & Next Sprint Plan
- `USER_FEEDBACK_AND_NEXT_SPRINT.md` — 6 real user-reported issues this
  sprint (not hypothetical), each with root cause and fix, plus a concrete
  Sprint 4 plan.

---

## ✅ Verification Commands

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v          # Expect: 438 passed
flake8 app/ --max-line-length=120   # Expect: 0 violations

cd ../frontend
npm run build              # Expect: build succeeds
npx eslint src/pages/administrator/Citizens.vue \
  src/pages/administrator/MunicipalAdministrators.vue \
  src/pages/administrator/FieldWorkers.vue \
  src/pages/administrator/Reports.vue \
  src/pages/administrator/AdminComplaintDetails.vue   # Expect: no output (clean)
```
