# Technical Documentation

> Last reviewed: 2026-07-21

This folder contains technical documentation for developers working on the Civic Services Platform.

## Contents

| Document | Description |
|---|---|
| `README.md` | This technical documentation index and implementation notes |
| `../../backend/README.md` | Backend setup and commands |
| `../../frontend/README.md` | Frontend setup and structure |
| `../../docs/api/README.md` | API behavior and endpoint conventions |
| `../../docs/database/README.md` | Database schema and ERD |
| `../../deployment/README.md` | Deployment guidance |

## Development Environment Setup

### Backend

1. Python 3.13+ required
2. Create and activate a virtual environment
3. Install dependencies from `requirements.txt`
4. Copy `.env.example` to `.env` and configure
5. Run `flask db upgrade` to apply migrations and create all tables
6. Run `flask seed` to create roles and the default system administrator
7. Run `flask import-pincodes` to load the `city_pincodes` master table from `database/pincode.csv`
8. Run `flask run` to start the development server

### Frontend

1. Node.js 22+ required
2. Run `npm install` in the `frontend/` directory
3. Copy `.env.example` to `.env` and configure
4. Run `npm run dev` to start the Vite dev server

## Environment Variables

### Backend (`.env`)

| Variable | Description | Example |
|---|---|---|
| `FLASK_ENV` | Environment name | `development` |
| `SECRET_KEY` | Flask secret key | `change-me-in-production` |
| `JWT_SECRET_KEY` | JWT signing key | `change-me-in-production` |
| `DATABASE_URL` | SQLAlchemy connection string (leave blank for SQLite) | `postgresql://user:pass@host/db` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173` |
| `ADMIN_EMAIL` | Default admin email for `flask seed` | `admin@civicservices.local` |
| `ADMIN_PASSWORD` | Default admin password for `flask seed` | `Admin@123456` |

## Project Timeline

| Milestone | Due Date | Focus |
|---|---|---|
| Milestone 1 | 28 June 2026 | User Stories |
| Milestone 2 | 22 July 2026 | Scheduling & Design |
| Milestone 3 (Sprint 1) | 2 August 2026 | API Development |
| Milestone 4 (Sprint 2) | 12 August 2026 | Testing & Integration |
| Milestone 5 | 23 August 2026 | Final Submission |

### Frontend (`.env`)

| Variable | Description | Example |
|---|---|---|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:5000/api/v1` |
| `VITE_APP_NAME` | Application name | `Civic Services Platform` |

## Documentation Backlog

- [ ] Add detailed backend developer guide
- [ ] Add frontend component development guide
- [ ] Document error handling strategy
- [ ] Document logging strategy

## Datetime Columns

All timestamp columns use `UTCDateTime` (`backend/app/utils/db_types.py`)
instead of plain `db.DateTime` — it guarantees every loaded value is
timezone-aware UTC, so `.isoformat()` always includes the `+00:00` offset.
When adding a new model column that stores a timestamp, import and use
`UTCDateTime` the same way, not `db.DateTime`, to avoid reintroducing the
naive-datetime timezone bug fixed in Milestone 4.

## Authentication Architecture (Current)

### Backend (OOP service layer)

- `AuthService` class (`backend/app/api/auth/service.py`) handles:
  - credential verification
  - JWT access/refresh token issuance
  - current-user retrieval
- `auth/controller.py` remains HTTP-focused and delegates business logic to `AuthService`.
- RBAC is centralized in decorators (`require_admin`, `require_system_admin`, `require_citizen`, `require_field_worker`).

### Frontend (store + service layering)

- `AuthService` class (`frontend/src/services/auth.service.js`) encapsulates auth API calls.
- `useAuthStore` (`frontend/src/stores/auth.js`) manages session state:
  - token persistence
  - user profile persistence
  - session hydration (`hydrateSession`) on first navigation
- Router guards (`frontend/src/router/index.js`) perform:
  - auth checks
  - guest checks
  - role checks
  - admin subtype checks
  - role-aware post-login routing

### Session Data Model

- `access_token` (JWT)
- `refresh_token` (JWT)
- `user` (`id`, `email`, `role`, `admin_level`, `city_name`, `full_name`, etc.)

## Administrator Hierarchy (Current)

The platform preserves the original 3-role model while splitting the administrator role internally:
- `Role.ADMINISTRATOR` remains the only administrator role value
- `AdministratorProfile.SYSTEM` identifies the default system administrator
- `AdministratorProfile.MUNICIPAL` identifies city-bound municipal administrators

Persistence model:
- `users`: authentication identity
- `administrator_profiles`: subtype and scope
- `cities`: municipality reference data

TPS-110 implementation details:
- municipal-administrator registration remains in `AdminService` to preserve the existing controller/service architecture
- administrator hierarchy data access now goes through `backend/app/repositories/administrator_repository.py`
- municipal-administrator create/update actions now write audit records through `backend/app/services/audit_log_service.py`
- the frontend uses the existing admin API rather than introducing a second registration or authentication flow
