# Database — Civic Services Platform

This folder contains database-related scripts, documentation, and seed data.

## Database Engine

**SQLite** (development) — file located at `backend/instance/civic.db`

## Migration Tool

**Alembic** via **Flask-Migrate** — migrations are stored in `backend/migrations/`.

## Initial Setup

```bash
cd backend

# Initialise the migrations folder (first time only)
flask db init

# Auto-generate migration from models
flask db migrate -m "initial schema"

# Apply migration
flask db upgrade
```

## Seed Data (Planned)

| File | Description |
|---|---|
| `seed_roles.py` | Create default roles (Citizen, Administrator, Field Worker) |
| `seed_users.py` | Create default admin and test users |

## Schema Reference

See [docs/database/README.md](../docs/database/README.md) for the full ERD.
