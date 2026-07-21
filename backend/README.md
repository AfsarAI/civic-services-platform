# Backend — Civic Services Platform

> Last reviewed: 2026-07-21

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

# 6. Seed roles + default admin user (idempotent — safe to re-run)
FLASK_APP=app.py flask seed

# 6b. Import city-pincode master data from database/pincode.csv
FLASK_APP=app.py flask import-pincodes

# 6c. Rebuild the mapping from scratch when needed
# FLASK_APP=app.py flask import-pincodes --replace

# 7. Run the development server
FLASK_APP=app.py FLASK_ENV=development flask run
```

**Swagger UI** → `http://localhost:5000/api/v1/docs`

> `flask seed` creates roles (`citizen`, `field_worker`, `administrator`) and a default
> admin account from your `.env` (`ADMIN_EMAIL` / `ADMIN_PASSWORD`). Safe to re-run.

> `flask import-pincodes` loads the `city_pincodes` master table from `database/pincode.csv`.
> Use `--replace` if you want to clear existing mappings before re-importing.

### Setup order

Run the backend setup in this order:

1. `FLASK_APP=app.py flask db upgrade`
2. `FLASK_APP=app.py flask seed`
3. `FLASK_APP=app.py flask import-pincodes`

If you need to refresh the mapping data, rerun step 3 with `--replace`.

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
│   ├── commands.py         # Flask CLI commands (flask seed, flask import-pincodes)
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
