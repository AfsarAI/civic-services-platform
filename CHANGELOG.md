# Changelog

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
- `complaint_assignments.evidence_url` column plus `POST /fieldworker/assignments/media` upload and serve endpoints for repair-completion photo evidence (TPS-89/TPS-90)
- City-scoped administrator hierarchy: municipal administrators now only see/act on complaints and field workers within their own city; system administrators remain unscoped
- Field worker management endpoints (`POST/GET/PUT/DELETE /admin/field-workers[/<id>]`), restricted to municipal administrators — system administrators cannot create field workers
- Real (non-placeholder) municipal-administrator dashboard summary (city-scoped complaint/worker counts) and administrator complaint table with working status/category filters and an inline assign-to-field-worker action
- `FieldWorkers.vue` field worker management page for municipal administrators (`/admin/field-workers`)
- Shared self-service `Profile.vue` for all 3 roles: editable name/phone (username/email read-only), profile photo upload (`users.avatar_url`, `POST/GET /auth/me/avatar[/<filename>]`), and a separate Change Password tab (`POST /auth/change-password`)

### Changed
- `flask seed` now creates a default System Administrator profile
- administrator reports and global user-management endpoints are restricted to the System Administrator subtype
- frontend admin routing and navigation now respect administrator subtype

---

## [0.1.0] - 2026-06-29

### Added
- Repository initialised
- Project structure created
- Base configuration files

[Unreleased]: https://github.com/<org>/civic-services-platform/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/<org>/civic-services-platform/releases/tag/v0.1.0
