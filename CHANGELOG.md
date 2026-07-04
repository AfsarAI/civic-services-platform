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
