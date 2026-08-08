# User Feedback & Next Sprint Plan — Milestone 4
## Sprint 3 Deliverable — Changes Made Based on User Feedback

**Project:** Civic Services Platform — Pothole Reporting and Resolution System
**Date:** 2026-08-08
**Sprint covered:** Sprint 3 (27 July – 9 August 2026)

---

## 1. How Feedback Was Gathered

Following the same approach as Milestone 3, "user feedback" this sprint came
from **live manual testing of the running application** by the team acting
as System Administrator, Municipal Administrator, Field Worker, and Citizen
in turn — not a synthetic/external pilot group. Each item below is a real,
reproduced issue found by clicking through the actual running UI/API, not a
hypothetical.

---

## 2. Feedback Received & Changes Made This Sprint

| # | Feedback (as reported) | Root Cause | Change Made |
|---|---|---|---|
| 1 | "In date time, time not showing correctly... admin assign complaint and give date and time, but on working page, time show 5:30 behind" | Plain `db.DateTime` columns store/load **naive** datetimes. `.isoformat()` on a naive datetime omits the UTC offset, and the browser's `new Date(...)` then misparses the offset-less string as **local** time — a fixed 5:30h (IST) drift on every timestamp in the app, not just assignments. | Added a `UTCDateTime` SQLAlchemy `TypeDecorator` (`backend/app/utils/db_types.py`) and applied it to every `DateTime` column across all 12 model files. No migration needed (`impl = DateTime` is unchanged) — every value now round-trips as tz-aware UTC, so existing `.isoformat()` calls everywhere automatically emit the correct `+00:00` suffix. Locked in with 2 new regression tests (see `TEST_CASE_DOCUMENTATION.md`). |
| 2 | "Even this complaint rejected, Actions is enabled and we can change Priority" — a rejected/closed complaint's Priority control and Update button were still clickable in `AdminComplaintDetails.vue` | The Priority edit block had no `v-if` gating on complaint status at all, unlike the Reject/Assign buttons which already correctly hid themselves on terminal statuses. | Added an `isTerminalStatus` computed (`status in ['closed', 'rejected']`) and wrapped the Priority section in `v-if="!isTerminalStatus"`, matching the pattern already used for Reject/Assign. The existing terminal-state message now also mentions priority. |
| 3 | "When System admin create municipal admin, or municipal administrator create worker account, he set password. But there is no way to reset password if municipal or worker or even citizen forget password" | Genuine missing feature — `POST /auth/change-password` requires the *current* password, so it's useless once forgotten, and no admin-assisted reset path existed at all. | Added optional `password`/`confirm_password` (+ `email`) fields to the three admin-facing update endpoints: `PUT /admin/users/{id}` (System Admin → any user, and now Municipal Admin → citizens in their own city), `PUT /admin/field-workers/{id}` (Municipal Admin → their field workers), `PUT /admin/municipal-administrators/{id}` (System Admin → municipal admins). No SMTP/email infrastructure required. See `openapi-with-user-stories.yaml` for full request/response docs and `TEST_CASE_DOCUMENTATION.md` for 11 new test cases. |
| 4 | Follow-up: "Citizens should also be manageable by both System Admin and Municipal Admin, not System Admin only" + "System Admin, Municipal Admin, [should be able to] change Name, Last name, phone no and email also... a separate update button, and to reset password a separate button" | `/admin/users` was `require_system_admin`-only and municipal admins had no way to see even their own city's citizens; the frontend combined profile-edit and password-reset into a single form/button on the Field Workers page. | (a) Changed `/admin/users` (list/get/put) to `require_admin`, with server-side city+role scoping for municipal admins (forced `role=citizen`, filtered to `admin_city_id`, 404 outside scope). (b) Added `email` to all three update schemas. (c) Split every admin management screen (`Citizens.vue` — new page, `MunicipalAdministrators.vue`, `FieldWorkers.vue`) into two independent actions: **"Edit Details"** (name/last name/email/phone) and **"Reset Password"**, each with its own button and form, per the explicit request. |
| 5 | "Reports page not working properly for system admin and municipal admin — No complaints match the currently applied filters" (shown even when data existed) | `hasReportData` was referenced 3 times in `Reports.vue`'s template but **never declared** in the script — always `undefined`, so `!hasReportData` was always `true`. | Added `const hasReportData = computed(() => (summary.value.total ?? 0) > 0)`. Verified via `npm run build` + manual check that the breakdown panels and CSV export button now correctly appear/enable when the summary has data. |
| 6 | "There was a setting [duplicate detection radius] on the System Settings page for duplicate report issue, and implementation also in Citizen and Admin, but now seems missing" | Not a regression from this sprint's own work. Git archaeology (`git log --full-history`, `git merge-base --is-ancestor`) traced the real sequence: the duplicate-detection feature was built and merged into `dev` once, then **explicitly reverted** via a PR, then **rebuilt a second time** on a local feature branch — but that rebuild's commit was authored *after* the branch had already been merged into `dev` at an earlier point, so the rebuilt version was never actually merged anywhere. It sat complete and untouched on a local branch, absent from `dev` and from this branch. | Identified the exact commit (`27ecb06`, 1402 insertions / 28 files, all 47 of its tests already passing) and reintegrated it via `git cherry-pick`. Resolved 2 real merge conflicts by hand (kept both the later `UTCDateTime` timezone fix *and* the new `duplicate_of_id`/`duplicate_reason` columns; kept both the assignment-notification method *and* the duplicate-detection methods in `AdminService`). Fixed a resulting migration-branching issue (two migrations sharing the same `down_revision`) by rebasing onto a single linear head. While verifying, found and fixed one more pre-existing bug: `SystemSettings.vue`'s `loadSettings()` never synced `duplicate_detection_radius_meters` from the server response, so the field always reset to the hardcoded default of 50 instead of showing the saved value. |

---

## 3. Issues Found & Fixed *During* This Sprint's Own Testing (not user-reported)

| # | Issue | How it was found | Resolution |
|---|---|---|---|
| 1 | `AdminService._ensure_email_available()` compared the candidate email against stored emails **without normalizing case**, so a case-differing duplicate email (e.g. `Name@Example.com` vs `name@example.com`) could silently overwrite another account's effective identity when the service was called directly (bypassing the Marshmallow schema's normalization, which is what a real HTTP request always goes through). | A new unit test (`test_update_municipal_administrator_rejects_duplicate_email`) failed on its first run — `pytest.raises(ValueError)` did not fire. | `_ensure_email_available()` now normalizes (`.strip().lower()`) internally and returns the canonical value; `update_user`, `update_field_worker`, and `update_municipal_administrator` all now assign the *returned* value rather than the raw input, so the check and the stored value can never disagree regardless of caller. Full before/after detail in `TEST_CASE_DOCUMENTATION.md`. |
| 2 | `GET /api/v1/reports/feedback/summary` existed in code and already had pytest coverage (`test_reports_api.py`), but was completely missing from `openapi-with-user-stories.yaml` — found via a full diff of the live Flask `url_map` against the documented paths. | Automated diff script comparing `app.url_map` to `api_mapping.json` keys, run as part of preparing this milestone's documentation. | Added the endpoint to both `openapi-with-user-stories.yaml` and `api_mapping.json`, mapped to TPS-96. |
| 3 | A previously-existing integration test (`test_municipal_admin_cannot_access_system_admin_user_list`) asserted the **old** behavior (municipal admins get 403 from `/admin/users`), which is now intentionally wrong given change #4 above. | Running the full suite after the `/admin/users` scoping change — this test failed as expected. | Rewrote the test as `test_municipal_admin_user_list_scoped_to_own_city_citizens`, asserting the new correct behavior (200 + city-scoped results) instead of just deleting the coverage. |
| 4 | Reintegrating the duplicate-detection feature (item #6 in Section 2) created two Alembic migrations (`7e2b9c4a1d3f` and `a1b2c3d4e5f6`) both pointing at the same `down_revision`, branching the migration history into two heads. | `flask db heads` showed 2 heads instead of 1 immediately after the cherry-pick. | Rebased `a1b2c3d4e5f6`'s `down_revision` onto `7e2b9c4a1d3f`, restoring a single linear head — same fix pattern as a similar issue documented from an earlier `dev` merge. |
| 5 | `SystemSettings.vue`'s `loadSettings()` never included `duplicate_detection_radius_meters` when copying the server response into the form, so the field silently always showed the hardcoded default (50) instead of the actually-saved value. | Manual verification of the restored feature after the cherry-pick, cross-checking the form's initial `reactive()` default against what `Object.assign` actually copies from `settings.value`. | Added the missing key to the `Object.assign(form, {...})` call. |
| 6 | Two tests (`test_dashboard_high_priority_pending_count_reflects_urgent_open_complaints`, `test_excel_export_is_valid_workbook`) failed once when run as part of the full 438-test suite, but passed both in isolation and on every other full-suite run. | Re-running the full suite twice after the cherry-pick to confirm stability. | Not fixed this sprint — flagged as pre-existing test-order/shared-DB-state flakiness (see Section 4.3) rather than masked or silently retried. |

---

## 4. Next Sprint Plan (Sprint 4: 10 August – 23 August 2026)

Per the project's 4-sprint structure, Sprint 4 focuses on **Reports,
notifications, testing & polish**, and leads into the Final Submission
milestone. Planned work:

### 4.1 Carry-over from Milestone 3's feedback (still open)
- [ ] Add a clear "wrong account type" message on the frontend when a 403 is
      returned for a role-gated route, instead of a silent redirect.
- [ ] Apply the KPI dashboard's date filter to the "Recent Complaints" list
      as well, so both stay in sync.
- [ ] Consolidate the KPI dashboard's duplicate field-name pairs
      (`avg_resolution_time_hours` vs `avg_resolution_hours`, etc.) to a
      single canonical set now that both consuming frontends are stable.

### 4.2 New feature work
- [ ] Citizen self-service "forgot password" was deliberately scoped out this
      sprint (no SMTP infrastructure) in favor of the admin-assisted reset
      delivered here — revisit if email delivery becomes available, so
      citizens don't strictly need to contact an administrator.
- [ ] Extend the `Users.vue`/`Citizens.vue`/`FieldWorkers.vue`/
      `MunicipalAdministrators.vue` "Edit Details" forms with basic optimistic
      UI feedback (currently a full list reload after every save).
- [ ] Add `openapi-spec-validator` as a CI check on `docs/milestone4/
      openapi-with-user-stories.yaml` (and future milestones) so an invalid
      spec fails the build automatically, rather than being caught manually
      (this milestone's YAML was validated manually with
      `openapi-spec-validator` before submission — see `00_SUBMISSION_INDEX.md`).

### 4.3 Process improvements
- [ ] Diff `app.url_map` against `api_mapping.json` as a standing pre-submission
      step for every future milestone (this is what caught the missing
      `/reports/feedback/summary` documentation this sprint) — codify as a
      small script rather than a one-off manual `python3 -c "..."` command.
- [ ] When a service method gains a new field that must be normalized
      (email, phone, etc.), write at least one **unit test that calls the
      service directly**, not just an integration test through the schema —
      this sprint's real bug (case-sensitive duplicate email) only surfaced
      because a unit test bypassed the schema's normalization layer.
- [ ] Investigate the two flaky full-suite-only test failures found this
      sprint (issue #6 in Section 3) — likely shared/leaking state between
      tests given the growing suite size (438 tests), not a code defect.
- [ ] Before deleting or switching away from a local feature branch, confirm
      its commits are actually reachable from `dev` (`git merge-base
      --is-ancestor <branch> origin/dev`), not just that a same-named PR was
      merged at some point — this sprint's missing duplicate-detection
      feature happened because a later commit on the branch was authored
      *after* an earlier snapshot of that branch had already been merged.

---

## 5. Sprint 3 Retrospective Summary

**What went well:**
- Every user-reported issue this sprint (6 items, Section 2) was reproduced
  first, root-caused, then fixed with an accompanying automated test —
  no fix was applied speculatively.
- The password-reset feature was scoped deliberately to avoid unnecessary
  infrastructure (no SMTP/email server needed) while still fully solving the
  reported problem for all three roles.
- Writing tests for the new service methods caught a real, non-obvious
  case-sensitivity bug before it reached the documented API surface.

**What could improve:**
- The `openapi-with-user-stories.yaml` documentation drifted from the live
  API again this sprint (`/reports/feedback/summary` missing) — the same
  class of gap noted in Milestone 3's retrospective. A standing url_map-diff
  script (Section 4.3) should close this permanently rather than relying on
  a manual pass at each milestone.
- Frontend template bugs referencing undeclared script variables (the
  `hasReportData` bug) are not caught by `npm run build` or ESLint by
  default in this project's config — worth investigating a stricter Vue
  template-checking lint rule for Sprint 4.

**Overall Sprint 3 Status:** ✅ All 6 user-reported issues fixed and verified
(including recovering a fully-built feature that had gone missing due to an
abandoned branch merge), 19 tests written + 47 tests reintegrated (438/438
passing, up from 372 at the start of this sprint's work), `flake8 app/`
clean, frontend `eslint`/`npm run build` clean, API documentation
(`openapi-with-user-stories.yaml`, `api_mapping.json`) brought back in sync
with the live API (60 documented paths).
