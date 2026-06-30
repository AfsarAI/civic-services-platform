# Backend — Civic Services Platform

Flask REST API for the Civic Services Platform.

## Quick Start

```bash
# Create your own local virtual environment (never committed to git)
python -m venv .venv

# Activate
source .venv/bin/activate        # WSL / Mac / Linux
# .venv\Scripts\activate         # Windows PowerShell

pip install -r requirements.txt
cp .env.example .env
flask db upgrade      # apply migrations (creates all tables)
flask seed            # create 3 roles + default admin user (idempotent)
flask run
```

> **`flask seed`** creates roles (`citizen`, `field_worker`, `administrator`) and a default
> admin account from your `.env` (`ADMIN_EMAIL` / `ADMIN_PASSWORD`). Safe to re-run.

## Structure

```
backend/
├── app/
│   ├── api/                # Flask-RESTX namespaces
│   │   ├── auth/           # Authentication (register, login, refresh, logout, me)
│   │   ├── citizen/        # Citizen complaint endpoints
│   │   ├── administrator/  # Admin complaint management, reports, user management
│   │   ├── fieldworker/    # Field worker task management
│   │   ├── reports/        # Analytics and exports
│   │   └── notifications/  # User notifications
│   ├── models/             # SQLAlchemy models (User, Role, Complaint, ...)
│   ├── schemas/            # Marshmallow validation schemas
│   ├── services/           # Business logic
│   ├── repositories/       # Data access layer
│   ├── extensions/         # Flask extensions (db, migrate, jwt, ma)
│   ├── commands.py         # Flask CLI commands (flask seed)
│   ├── config/             # App config helpers
│   └── utils/              # Shared decorators (validate_body, require_role)
├── migrations/             # Alembic migrations
├── tests/
│   ├── unit/
│   └── integration/
├── instance/               # SQLite DB (git-ignored)
├── app.py                  # Entry point
├── config.py               # Configuration classes
└── requirements.txt
```

## API Documentation

Start the server and visit: `http://localhost:5000/api/docs`

## Running Tests

```bash
pytest tests/ --cov=app -v
```
