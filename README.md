# Civic Services Platform

A university Scrum project — an enterprise-grade web platform that allows **citizens** to report potholes and civic issues, **administrators** to manage and assign complaints, and **field workers** to update repair progress in real time.

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
| **Citizen** | Register, submit complaints (potholes, etc.), track status, provide feedback |
| **Administrator** | View all complaints, assign field workers, manage users, generate reports |
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

- **Node.js** >= 18.x
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

# Each developer creates their own local venv — never committed to git
python -m venv .venv

source .venv/bin/activate        # WSL / Mac / Linux
# .venv\Scripts\activate         # Windows PowerShell

pip install -r requirements.txt
cp .env.example .env
flask run
```

The API will be available at `http://localhost:5000`.

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
http://localhost:5000/api/docs
```

All namespaces and endpoints are documented via **Flask-RESTX** Swagger UI.

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
| TBD | Scrum Master | @tbd |
| TBD | Product Owner | @tbd |
| TBD | Frontend Developer | @tbd |
| TBD | Backend Developer | @tbd |
| TBD | Full Stack Developer | @tbd |

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
