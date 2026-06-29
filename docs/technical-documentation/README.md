# Technical Documentation

This folder contains technical documentation for developers working on the Civic Services Platform.

## Contents

| Document | Description |
|---|---|
| `backend-setup.md` | Backend development setup guide |
| `frontend-setup.md` | Frontend development setup guide |
| `api-conventions.md` | API design and naming conventions |
| `database-guide.md` | Database schema and migration guide |
| `authentication.md` | JWT authentication implementation details |
| `deployment.md` | Deployment procedures |

## Development Environment Setup

### Backend

1. Python 3.13+ required
2. Create and activate a virtual environment
3. Install dependencies from `requirements.txt`
4. Copy `.env.example` to `.env` and configure
5. Run `flask db upgrade` to apply migrations
6. Run `flask run` to start the development server

### Frontend

1. Node.js 18+ required
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
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///civic.db` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173` |

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

## TODO

- [ ] Add detailed backend developer guide
- [ ] Add frontend component development guide
- [ ] Document error handling strategy
- [ ] Document logging strategy
