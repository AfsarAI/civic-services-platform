# Backend — Civic Services Platform

Flask REST API for the Civic Services Platform.

## Quick Start

```bash
# 1. Create your own local virtual environment (never committed to git)
python -m venv .venv

# 2. Activate
source .venv/bin/activate        # WSL / Mac / Linux
# .venv\Scripts\activate         # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create local .env from template
cp .env.example .env
# Open .env and set SECRET_KEY and JWT_SECRET_KEY to random strings

# 5. Apply DB migrations (creates all tables in instance/civic.db)
FLASK_APP=app.py flask db upgrade

# 6. Seed roles + default system administrator (idempotent — safe to re-run)
FLASK_APP=app.py flask seed

# 7. Run the development server
FLASK_APP=app.py FLASK_ENV=development flask run
```

**Swagger UI** → `http://localhost:5000/api/v1/docs`

> `flask seed` creates roles (`citizen`, `field_worker`, `administrator`) and a default
> **System Administrator** account from your `.env` (`ADMIN_EMAIL` / `ADMIN_PASSWORD`).
> Safe to re-run.

## Administrator Hierarchy

The backend does **not** introduce a fourth role such as `system_admin`.

Instead:
- `users` still stores the coarse application role
- `administrator_profiles` stores the administrator subtype
- `cities` stores the city for municipal administrators

Current administrator subtypes:
- `system`: global platform administration
- `municipal`: administrator assigned to exactly one city

Auth contract remains unchanged:
- one login endpoint: `POST /api/v1/auth/login`
- email/password authentication
- both admin subtypes are returned with `role: "administrator"`
- extra user metadata now includes `admin_level`, `city_id`, and `city_name`

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

Start the server and visit: `http://localhost:5000/api/v1/docs`

## Running Tests

```bash
pytest tests/ --cov=app -v
```
