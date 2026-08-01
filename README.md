# Civic Services Platform

> Last reviewed: 2026-07-21

A university Scrum project — an enterprise-grade web platform that lets **citizens** report potholes with a photo and map location, **administrators** manage and assign complaints, and **field workers** update repair progress in real time.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [Running the Frontend](#running-the-frontend)
- [Running the Backend](#running-the-backend)
- [Database Migration](#database-migration)
- [API Documentation (Swagger)](#api-documentation-swagger)
- [Git Workflow](#git-workflow)
- [Sprint Structure](#sprint-structure)
- [Contributors](#contributors)

---

## Project Overview

The **Civic Services Platform** enables:

| Role | Capabilities |
|---|---|
| **Citizen** | Register, submit pothole complaints with photo and location, track status, provide feedback |
| **Administrator** | System Administrator and Municipal Administrator accounts share the same `administrator` role, with subtype-based permissions |
| **Field Worker** | View assigned tasks, update repair progress, upload evidence |

**Development Methodology:** Scrum
**Version Control:** Git + GitHub
**Issue Tracking:** Jira

---

## Technology Stack

### Frontend

| Technology | Version | Purpose |
|---|---|---|
| Vue 3 | ^3.4 | UI Framework |
| Vue Router | ^4.3 | Client-side Routing |
| Pinia | ^2.1 | State Management |
| Tailwind CSS | ^3.4 | Utility-first CSS |
| Axios | ^1.7 | HTTP Client |
| Vite | ^5.x | Build Tool |

### Backend

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.13+ | Runtime |
| Flask | ^3.x | Web Framework |
| Flask-RESTX | ^1.3 | REST API + Swagger UI |
| Flask-SQLAlchemy | ^3.x | ORM |
| Flask-Migrate | ^4.x | Database Migrations |
| Marshmallow | ^3.x | Serialization / Validation |
| Flask-JWT-Extended | ^4.x | JWT Authentication |
| Flask-CORS | ^4.x | Cross-Origin Resource Sharing |
| python-dotenv | ^1.x | Environment Variables |

### Database

| Technology | Purpose |
|---|---|
| SQLite | Development Database |
| SQLAlchemy | ORM |
| Alembic (via Flask-Migrate) | Schema Migrations |

---

## Folder Structure

```
/
├── .github/
│   ├── workflows/
│   │   ├── frontend-ci.yml
│   │   └── backend-ci.yml
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── pull_request_template.md
├── docs/
│   ├── architecture/
│   ├── database/
│   ├── api/
│   ├── ui/
│   ├── sprint/
│   ├── meetings/
│   │   ├── SprintPlanning/
│   │   ├── DailyScrum/
│   │   ├── SprintReview/
│   │   └── SprintRetrospective/
│   ├── testing/
│   ├── user-manual/
│   └── technical-documentation/
├── frontend/                    # Vue 3 + Vite application
├── backend/                     # Flask REST API
├── database/                    # DB scripts and ERD
├── postman/                     # Postman collections
├── deployment/                  # Deployment configurations
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── .gitignore
```

---

## Installation

### Prerequisites

- **Node.js** >= 22.x
- **Python** >= 3.13
- **pip** >= 23.x
- **Git**

---

## Running the Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## Running the Backend

```bash
cd backend

# 1. Create your own local virtual environment (never committed to git)
python -m venv .venv

# 2. Activate the virtual environment
source .venv/bin/activate        # WSL / Mac / Linux
# .venv\Scripts\activate         # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your local .env from the example
cp .env.example .env
# Edit .env and set SECRET_KEY and JWT_SECRET_KEY to random strings

# 5. Apply database migrations (creates all tables)
FLASK_APP=app.py flask db upgrade

# 6. Seed roles and default admin user (safe to re-run)
FLASK_APP=app.py flask seed

# 6b. Import city/pincode mappings from database/pincode.csv
FLASK_APP=app.py flask import-pincodes

# 7. Start the development server
FLASK_APP=app.py FLASK_ENV=development flask run
```

### Code Quality — Flake8 Analysis

```bash
cd backend

# Run Flake8 with project's standard (120 char line limit)
python3 -m flake8 app/ --max-line-length=120

# Run with PEP 8 strict mode (79 char limit)
python3 -m flake8 app/

# Generate detailed report
python3 -m flake8 app/ --max-line-length=120 --count --statistics
```

**Status:** ✅ 0 violations with `--max-line-length=120` | ⚠️ 149 E501 violations with PEP 8 default (79 chars)

See [Software_Metrics_Report_Flake8.md](Software_Metrics_Report_Flake8.md) for detailed analysis.

### Database setup order

Run these backend commands in order after creating `.env`:

1. `FLASK_APP=app.py flask db upgrade`
2. `FLASK_APP=app.py flask seed`
3. `FLASK_APP=app.py flask import-pincodes`

Use `FLASK_APP=app.py flask import-pincodes --replace` if you want to clear and reload the `city_pincodes` table from `database/pincode.csv`.

The API will be available at `http://localhost:5000`.

> **Swagger UI** (interactive API docs): `http://localhost:5000/api/v1/docs`

> **Default system administrator credentials** (set in `.env` before running `flask seed`):
> Email: `admin@civicservices.local` | Password: `Admin@123456`

## Administrator Hierarchy

The platform still uses exactly **3 application roles** in the `roles` table:
- `citizen`
- `administrator`
- `field_worker`

The administrator role is now split internally using an administrator profile:
- **System Administrator**
  - created by default through `flask seed`
  - can create, manage, and disable Municipal Administrators
  - can view all cities
  - can access global reports and platform-wide user management
- **Municipal Administrator**
  - belongs to exactly one city
  - cannot self-register
  - is created only by the System Administrator
  - logs in through the same `/auth/login` endpoint and is still returned as role `administrator`
  - can be managed from the System Administrator UI at `/admin/municipal-administrators`

Implementation summary:
- `users.role_id` remains unchanged
- new `cities` table stores administrative cities
- new `administrator_profiles` table stores `admin_level` and `city_id`
- JWT and `/auth/me` now include `admin_level`, `city_id`, and `city_name`
- frontend routing remains role-based, with subtype-aware restrictions for system-only pages
- municipal-admin registration now uses the existing admin API with audit logging and validation parity for password and phone fields

## Recent Changes

- Narrowed the product scope to pothole-only reporting.
- Made complaint photo upload mandatory in the citizen flow.
- Reworked the mobile report screen around photo, map pin, pincode, and city selection.
- Added backend support for uploading complaint photos and serving them back by URL.
- Added the `flask import-pincodes` command for loading `city_pincodes` from `database/pincode.csv`.
- Updated the documentation set to match the current setup order and database seeding flow.

---

## Database Migration

```bash
cd backend

# Initialise migrations (first time only)
flask db init

# Generate a migration
flask db migrate -m "initial schema"

# Apply migrations
flask db upgrade
```

---

## API Documentation (Swagger)

Once the backend is running, open:

```
http://localhost:5000/api/v1/docs
```

All namespaces and endpoints are documented via **Flask-RESTX** Swagger UI.

### Using Swagger with JWT

Most endpoints require authentication. Follow these steps to authorise in Swagger UI:

**Step 1 — Get a token**

Call `POST /auth/login` with your credentials:
```json
{
  "email": "admin@civicservices.local",
  "password": "Admin@123456"
}
```
Copy the `access_token` value from the response.

**Step 2 — Authorise in Swagger**

1. Click the **Authorize 🔒** button at the top right of the Swagger UI page
2. In the **Bearer** field enter: `Bearer <paste_your_token_here>`
3. Click **Authorize** → **Close**

**Step 3 — Use protected endpoints**

All endpoints marked with a 🔒 padlock icon are now accessible. The token is sent automatically in the `Authorization` header with every request.

> Tokens expire after **1 hour**. Repeat Step 1–2 when you see a `401 Unauthorised` response.
> Use `POST /auth/refresh` with your `refresh_token` to get a new access token without logging in again.

---

## Git Workflow

We follow **GitHub Flow** adapted for Scrum sprints.

### Branch Naming Convention

| Branch | Purpose |
|---|---|
| `main` | Production-ready code — never develop directly here |
| `dev` | Integration branch — all features merge here first |
| `feature/<rollno>-<jiraid>-story-title` | One branch per Jira story |

**Branch protection rules apply to both `main` and `dev`:**
- Require Pull Request before merging
- No direct push
- Minimum 1 approval (Scrum Master or Project Manager)

### Commit Message Format

```
<type>(<scope>): <subject>

Types: feat | fix | docs | style | refactor | test | chore
```

**Examples:**

```
feat(auth): add JWT login endpoint
fix(citizen): resolve complaint submission validation
docs(readme): update installation instructions
```

### Development Flow

```
Step 1  Create feature branch from dev
        feature/<rollno>-<jiraid>-story-title

Step 2  Develop → Commit → Push

Step 3  Open Pull Request:  feature → dev
        Scrum Master or Project Manager reviews → Approve → Merge

Step 4  After Sprint:
        Open Pull Request:  dev → main
```

### Pull Request Process

1. Create a branch from `dev`
2. Implement changes with tests
3. Open a Pull Request using the PR template
4. Get at least **1 code review approval** (Scrum Master or Project Manager)
5. All CI checks must pass
6. Merge via **Squash and Merge**
7. After sprint completion — merge `dev` → `main`

---

## Milestones

| # | Milestone | Due Date | Focus |
|---|---|---|---|
| 1 | User Identification & User Stories | 28 June 2026 | Requirements |
| 2 | Scheduling & Design | 22 July 2026 | Design + UI |
| 3 | Sprint 1 — API Development | 2 August 2026 | Backend APIs |
| 4 | Sprint 2 — Testing & Integration | 12 August 2026 | Tests + Integration |
| 5 | Final Submission | 23 August 2026 | Complete project |

---

## Sprint Structure

This project follows a **2-week Scrum sprint** cycle with **4 sprints**.

| Sprint | Dates | Focus |
|---|---|---|
| Sprint 1 | 29 June – 12 July 2026 | Project setup, authentication, core models |
| Sprint 2 | 13 July – 26 July 2026 | Citizen complaint submission & tracking |
| Sprint 3 | 27 July – 9 August 2026 | Admin management, field worker progress |
| Sprint 4 | 10 August – 23 August 2026 | Reports, notifications, testing & polish |

| Scrum Ceremony | Frequency | Duration |
|---|---|---|
| Sprint Planning | Start of sprint | 2 hours |
| Daily Scrum | Daily | 15 minutes |
| Sprint Review | End of sprint | 1 hour |
| Sprint Retrospective | End of sprint | 45 minutes |

Sprint documentation is stored under `docs/meetings/`.

---

## Contributors

| Name | Role | GitHub |
|---|---|---|
| Gautham (21f3002294) | Team Member | @21f3002294 |
| MOHD AFSAR (23f2002023) | Team Member | @23f2002023 |
| RAHUL VERMA (21f1001325) | Team Member | @21f1001325 |
| HAFIZA NOOR (23f2004875) | Team Member | @23f2004875 |
| Jitendra Kumar (23f1000704) | Team Member | @23f1000704 |

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
