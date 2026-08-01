# User Feedback & Next Sprint Plan
## Sprint 1 & 2 Deliverable #6 — Milestone 3

**Project:** Civic Services Platform — Pothole Reporting and Resolution System
**Date:** 2026-08-01
**Sprints covered:** Sprint 1 (29 June – 12 July) and Sprint 2 (13 July – 26 July)

---

## 1. How Feedback Was Gathered

Since the platform is a team-internal Scrum project without an external pilot
group at this stage, "user feedback" for Sprint 1 & 2 was gathered through:

1. **Sprint Review demos** — each of the 3 role-based portals (citizen,
   field worker, administrator) walked through end-to-end against the
   Jira acceptance criteria at the end of each sprint.
2. **API-level testing** — 182 pytest test cases (integration + unit)
   exercising every implemented endpoint, surfacing real validation/behaviour
   gaps before they reached a UI reviewer.
3. **Manual/live smoke testing** — the reviewer (acting as System
   Administrator, Municipal Administrator, Field Worker, and Citizen in turn)
   exercised the running dev server directly (login, dashboard, complaint
   lifecycle, report export) rather than relying only on automated tests.
4. **Cross-branch integration review** — merging the `dev` integration branch
   surfaced real usability/consistency issues between features built by
   different team members in parallel (see Section 3).

---

## 2. Key Feedback Themes

### 2.1 Positive Feedback
- **Photo-first complaint reporting** (mandatory photo + map pin) was
  confirmed to work smoothly end-to-end and matches the "pothole-only" scope
  decision.
- **City-scoping** for municipal administrators (complaints, field workers,
  reports) behaves correctly and consistently across every namespace it
  touches — no city-boundary leaks were found in testing.
- **Notification coverage** is now genuinely event-driven (not a placeholder)
  across the full complaint lifecycle: submit → assign → accept → complete →
  verify → resolve/close, with the complaint ID embedded in every message as
  required by TPS-91 AC3.
- **Report export** (CSV/Excel/PDF) was validated against a live server with
  real downloaded files inspected byte-for-byte, not just unit-tested in
  isolation — this caught a subtle CSV/Excel formatting issue early.

### 2.2 Issues Found & Fixed During Review
| # | Issue | How it was found | Resolution |
|---|---|---|---|
| 1 | `avg_resolution_time_hours` on the KPI dashboard only counted complaints still in `resolved` status, silently excluding ones later moved to `closed`, while the pre-existing Reports summary counted both — a live smoke test against the real dev DB showed the two numbers disagreeing for the same data. | Live smoke test comparing `/admin/dashboard` vs `/reports/complaints/summary` on identical data | `AdminService._calculate_avg_resolution_time` corrected to match the Reports definition; verified both endpoints now report the same figure |
| 2 | Merging `dev` produced 2 real merge conflicts (`administrator/service.py`, `AdministratorDashboard.vue`) because two team members had independently extended the same `GET /admin/dashboard` endpoint (TPS-97 Performance Metrics vs TPS-95 View Dashboard) | Git merge | Manually reconciled: kept both KPI field sets for backward compatibility, combined the KPI cards UI with the new status-breakdown chart, removed now-dead duplicate code (a redundant `stats` computed property, duplicate `loadingDashboard` declaration), and added a missing `onBeforeUnmount` cleanup for the dashboard auto-refresh timer that the original implementation was missing |
| 3 | After merging `dev`, every complaint-related endpoint (reports, admin complaint list) returned `HTTP 500 sqlite3.OperationalError: no such column: complaints.closed_at` | Manual testing against the local dev server immediately after merge | Root cause: `dev` added a `Complaint.closed_at` column + Alembic migration, but `flask db upgrade` had not been re-run locally. Documented as a repeatable gotcha: re-run `flask db upgrade` after any merge that touches `backend/migrations/versions/`, not just on first setup |
| 4 | Several TPS (Jira story) references in the API documentation were factually wrong — e.g. `/reports/complaints/by-priority` was tagged `TPS-57` (actually "Create ER Diagram", an unrelated design task) | Cross-checking every TPS number against `docs/project-guide/Jira.csv` while updating the OpenAPI docs for this deliverable | All TPS mappings in `openapi-with-user-stories.yaml` and `api_mapping.json` corrected and verified against the ground-truth Jira export; corrections are called out explicitly in the YAML's summary table |
| 5 | The field-worker "update progress" endpoint was documented under a path (`/fieldworker/assignments/{id}/update`) that doesn't exist on the server — the real route is `PUT` on the same path as the `GET` (`/fieldworker/assignments/{id}`) | Diffing the documented paths against the live Flask route table | Documentation corrected; this was a docs-only bug, the actual frontend/backend code was already calling the correct route |
| 6 | Response envelope's `errors` field was documented as OpenAPI `type: "null"`, which is not valid OpenAPI 3.0 (fails schema validation) | Running `openapi-spec-validator` against the curated YAML as part of this deliverable | Changed to `{ type: "object", nullable: true }`; file now validates cleanly |

### 2.3 Usability Observations for Future Sprints
- Citizens and field workers currently have **no in-app way to tell they've
  been assigned the wrong role** (e.g. a citizen navigating to `/admin/...`
  gets a clean 403, but the failure mode isn't always obvious from the UI —
  worth a friendlier "wrong account type" banner instead of a silent redirect).
- The KPI dashboard's **date filter** currently only filters the KPI numbers,
  not the "Recent Complaints" list underneath it — minor inconsistency to fix.
- Municipal administrators have no self-service way to see *why* a field
  worker assignment failed validation (e.g. wrong city) beyond the raw error
  message — could be clearer in the UI.

---

## 3. Next Sprint Plan (Sprint 3: 27 July – 9 August)

Per the project's 4-sprint structure, Sprint 3 focuses on **Admin management,
field worker progress** — building on the API/testing foundation delivered in
Sprint 1 & 2. Planned work:

### 3.1 Carry-over fixes from feedback (Section 2.3)
- [ ] Add a clear "wrong account type" message on the frontend when a 403 is
      returned for a role-gated route, instead of a silent redirect.
- [ ] Apply the KPI dashboard's date filter to the "Recent Complaints" list
      as well, so both stay in sync.
- [ ] Surface the field-worker city-mismatch validation error more clearly in
      the assignment UI (currently a generic error banner).

### 3.2 New feature work
- [ ] Extend automated test coverage to the frontend (currently backend-only
      via pytest) — at minimum smoke tests for the citizen report flow and
      the admin assignment flow.
- [ ] Add WebSocket or short-polling based **real-time** notification delivery
      to replace/augment the current 30-second dashboard polling interval,
      reducing perceived latency for admins monitoring live complaint status.
- [ ] Revisit the KPI dashboard's dual field sets (`avg_resolution_time_hours`
      vs `avg_resolution_hours`, `high_priority_pending_count` vs
      `high_priority_complaints`) introduced by the `dev` merge — consolidate
      to a single canonical field set once both consuming frontends are
      confirmed stable, to reduce API surface confusion for future
      maintainers.
- [ ] Audit and correct any remaining incorrect TPS-story cross-references
      elsewhere in the codebase/docs beyond what was fixed in this pass
      (the API documentation was corrected; a similar audit of code comments
      referencing TPS numbers has not yet been done).

### 3.3 Process improvements
- [ ] Re-run `flask db upgrade` as a documented step in the PR checklist
      whenever a PR touches `backend/migrations/versions/`, to prevent the
      "no such column" class of post-merge failures found this sprint.
- [ ] Add `openapi-spec-validator` (or an equivalent CI check) to the backend
      CI pipeline so an invalid Swagger/OpenAPI document fails the build
      automatically, rather than being caught manually during a
      documentation pass.

---

## 4. Sprint 1 & 2 Retrospective Summary

**What went well:**
- Core complaint lifecycle (submit → assign → accept → complete → verify →
  resolve/close) is fully implemented, notification-integrated, and
  100% covered by passing automated tests.
- City-scoping and the administrator hierarchy (system vs municipal) are
  consistently enforced across every namespace, with no gaps found during
  a full manual audit.
- Report generation, analytics, KPI dashboard, and report export (CSV/Excel/
  PDF) are all implemented and independently verified via both pytest and a
  live smoke test.

**What could improve:**
- Parallel feature branches independently extending the same endpoint
  (`/admin/dashboard`) caused avoidable merge friction — future sprints
  should flag when two in-flight stories touch the same file/endpoint early
  in planning.
- Some TPS story-number references in documentation drifted from the actual
  Jira backlog over time; documentation should be cross-checked against
  `Jira.csv` as a habit, not just at final submission time.

**Overall Sprint 1 & 2 Status:** ✅ All required deliverables complete,
182/182 automated tests passing, all endpoints documented and verified.
