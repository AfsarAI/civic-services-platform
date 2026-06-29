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
flask db upgrade
flask run
```

## Structure

```
backend/
├── app/
│   ├── api/                # Flask-RESTX namespaces
│   │   ├── auth/           # Authentication endpoints
│   │   ├── citizen/        # Citizen endpoints
│   │   ├── administrator/  # Admin endpoints
│   │   ├── fieldworker/    # Field worker endpoints
│   │   ├── reports/        # Reports endpoints
│   │   └── notifications/  # Notifications endpoints
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Marshmallow schemas
│   ├── services/           # Business logic (placeholder)
│   ├── repositories/       # Data access layer (placeholder)
│   ├── extensions/         # Flask extensions
│   ├── config/             # App config helpers
│   └── utils/              # Utilities & decorators
├── migrations/             # Alembic migrations
├── tests/
│   ├── unit/
│   └── integration/
├── instance/               # SQLite DB (git-ignored)
├── app.py                  # Entry point
├── config.py               # Configuration
└── requirements.txt
```

## API Documentation

Start the server and visit: `http://localhost:5000/api/docs`

## Running Tests

```bash
pytest tests/ --cov=app -v
```
