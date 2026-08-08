# Changelog

> Last reviewed: 2026-07-21

All notable changes to the **Civic Services Platform** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Initial project scaffold
- Vue 3 frontend with Vite
- Flask backend with Flask-RESTX
- SQLAlchemy + SQLite database configuration
- JWT authentication foundation
- Role-based access control stubs (Citizen, Administrator, Field Worker)
- CI/CD GitHub Actions workflows
- Swagger UI documentation
- Postman collection skeleton
- `cities` table for municipal assignment
- `administrator_profiles` table for administrator subtype separation
- System Administrator and Municipal Administrator hierarchy inside the existing `administrator` role
- system-admin-only municipal administrator management endpoints
- JWT and `/auth/me` metadata for `admin_level`, `city_id`, and `city_name`
- Full field worker portal: `FieldWorkerDashboard.vue` (stats + filterable/paginated assignment list) and `AssignmentDetails.vue` (accept, start progress, reject, complete with optional photo evidence), matching citizen/administrator dashboard look and feel
- `complaint_assignments.evidence_url` column plus `POST /fieldworker/assignments/media` upload and serve endpoints for repair-completion photo evidence (TPS-89)
- City-scoped administrator hierarchy: municipal administrators now only see/act on complaints and field workers within their own city; system administrators remain unscoped
- Field worker management endpoints (`POST/GET/PUT/DELETE /admin/field-workers[/<id>]`), restricted to municipal administrators — system administrators cannot create field workers
- Real (non-placeholder) municipal-administrator dashboard summary (city-scoped complaint/worker counts) and administrator complaint table with working status/category filters and an inline assign-to-field-worker action
- `FieldWorkers.vue` field worker management page for municipal administrators (`/admin/field-workers`)
- Shared self-service `Profile.vue` for all 3 roles: editable name/phone (username/email read-only), profile photo upload (`users.avatar_url`, `POST/GET /auth/me/avatar[/<filename>]`), and a separate Change Password tab (`POST /auth/change-password`)
- Admin complaint status-transition workflow (TPS-81/82/83/84): priority updates, `in_progress→resolved→closed` verification flow, and reject-at-any-pre-terminal-stage, enforced server-side in `AdminService._ADMIN_STATUS_TRANSITIONS`
- `AdminComplaintDetails.vue` (`/admin/complaints/:id`): full monitor/verify/close/reject/prioritize/assign screen, replacing the need to guess complaint state from the dashboard table alone
- Real notification delivery: `NotificationService.send_notification()` now actually fires on complaint assignment, field-worker accept, field-worker reject, and admin resolve/close/reject — previously defined but never called
- Notifications frontend: working bell dropdown in `Navbar.vue` (unread badge, 30s poll, mark-as-read/mark-all-read) and a full `/notifications` page, replacing the static placeholder bell icon
- Real `Reports.vue` wired to all 5 existing `/reports` endpoints (summary cards, by-status/by-category bars, trends bar chart, worker performance table), replacing the "coming soon" placeholders
- System Settings (TPS-99): new `system_settings` singleton table, `GET/PUT /admin/settings` (system admin only, audit-logged, validated), with two settings carrying real runtime effect — `maintenance_mode` (blocks non-administrator logins) and `notify_on_status_change` (gates all automatic notification sends); `SystemSettings.vue` page for system administrators
- Citizen edit-complaint UI (TPS-74): `ComplaintDetails.vue` now has a full in-place "Edit complaint" mode (visible only while `status === pending`) for description, road/street name, pothole location (draggable Leaflet map pin), and photo (re-upload), wired to the existing `PUT /citizen/complaints/<id>` endpoint — previously the endpoint had no citizen-facing UI at all
- Cancel complaint (TPS-75): new `Complaint.STATUS_CANCELLED`; `DELETE /citizen/complaints/<id>` now soft-cancels (preserves the row, sets `status=cancelled`) instead of hard-deleting, so cancelled complaints remain visible in history and reports but are permanently excluded from assignment. Cancel action with a confirmation dialog added to `TrackComplaint.vue` and `ComplaintDetails.vue`; `cancelled` status badge/filter/timeline support added across citizen and administrator views
- Feedback UI upgrade (TPS-77): `ComplaintDetails.vue` feedback form replaced with a clickable 1-5 star rating widget, an explicit success/error message, and a "Submitted on" timestamp on the confirmation card; `TrackComplaint.vue`'s dead-end "Add feedback" stub (which just displayed a static message with no way to actually submit) now links directly to the working feedback form. New standalone test file `test_citizen_feedback_api.py` covering all 6 acceptance criteria end to end
- Citizen status-change notifications (TPS-91) completed end to end: notification now sent on complaint submission (previously missing entirely) and on repair completion (previously only the administrator was notified); every citizen/worker/admin-facing notification message now embeds the Complaint ID (`#<id>`), and both the navbar bell dropdown and the `/notifications` page render an explicit "Complaint #<id>" badge
- Reports (TPS-85/96/97/98) opened up to municipal administrators, scoped to their own city, instead of system-administrator-only; added `date_from`/`date_to` and `status` query-param filters across all report endpoints; added new "Complaints by Priority" and "Complaints by Location" breakdowns; `Reports.vue` gained a filter bar and a client-side "Export CSV" button. New `test_reports_api.py` test file (previously no report test coverage existed)

- Field worker dashboard (TPS-86) gained search (by title/street/complaint ID), a priority filter alongside the existing status filter, and sort controls (by assignment date or priority, ascending/descending); the assignment table now also shows Reported Date, Location, Road/Street Name, and Expected Completion Date, all previously missing from the UI despite the backend already having the data
- New Work History page (TPS-90) at `/fieldworker/history`: a dedicated, searchable/filterable/sortable view of all past and current assignments (separate from the action-oriented Dashboard), showing Completion Date and Repair Remarks columns; reuses the existing assignments API with no backend changes required
- Assignment notifications for field workers now include structured assignment context in the message (complaint ID, assignment date/time, location, priority, expected completion, and optional administrator remarks), expose `related_assignment_id`, and are idempotent per assignment event to avoid duplicates
- Administrator-driven password reset and email update: `PUT /admin/users/{id}`, `PUT /admin/field-workers/{id}`, and `PUT /admin/municipal-administrators/{id}` now accept optional `email` and `password`/`confirm_password` fields, giving System Administrators and Municipal Administrators a way to recover a forgotten password or correct an email for the accounts they manage, without any SMTP/email infrastructure
- `/admin/users` (list/get/update) opened up to Municipal Administrators, automatically scoped to citizens in their own city (System Administrators remain unscoped across every role)
- New `Citizens.vue` page (`/admin/citizens`) — citizen account management (view, edit details, reset password) for System Administrators (all citizens) and Municipal Administrators (their own city's citizens only)
- Frontend admin management screens (`Citizens.vue`, `MunicipalAdministrators.vue`, `FieldWorkers.vue`) now expose "Edit Details" (name/last name/email/phone) and "Reset Password" as two separate, independent actions instead of one combined form

### Fixed
- **Timezone display bug**: all `DateTime` columns switched from plain `db.DateTime` to a new `UTCDateTime` SQLAlchemy type (`backend/app/utils/db_types.py`, no migration required) — previously every timestamp returned by the API was naive (no UTC offset), which the frontend's `new Date(...)` misparsed as local time, displaying every date/time 5:30 hours behind (IST)
- `AdminComplaintDetails.vue`: the Priority edit control and "Update priority" button are now correctly hidden once a complaint reaches a terminal status (`rejected`/`closed`), matching the existing gating already applied to the Reject/Assign actions
- `Reports.vue`: fixed a bug where the `hasReportData` computed was referenced in the template but never declared in the script (always `undefined`/falsy), causing "No complaints match the currently applied filters" to show unconditionally even when report data existed
- `AdminService._ensure_email_available()` now normalizes (trims/lower-cases) the candidate email itself and returns the canonical value for storage, fixing a case-sensitivity gap where a duplicate email differing only by letter case could bypass the uniqueness check when a service method was called directly (found by a new unit test)

### Changed
- `flask seed` now creates a default System Administrator profile
- administrator reports and global user-management endpoints are restricted to the System Administrator subtype
- frontend admin routing and navigation now respect administrator subtype
- refreshed repository documentation (`README.md`, `docs/**/*.md`, and setup guides) to align Jira keys (`TPS-*`), location schema docs, and current complaint lifecycle rules

---

## [0.1.0] - 2026-06-29

### Added
- Repository initialised
- Project structure created
- Base configuration files

[Unreleased]: https://github.com/<org>/civic-services-platform/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/<org>/civic-services-platform/releases/tag/v0.1.0
