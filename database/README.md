# Database — Civic Services Platform

> Last reviewed: 2026-07-21

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

# Seed roles and default admin user
flask seed

# Import city/pincode mappings from CSV into city_pincodes
flask import-pincodes
```

## Seed Data

| File | Description |
|---|---|
| `seed_roles.py` | Create default roles (Citizen, Administrator, Field Worker) |
| `seed_users.py` | Create default admin and test users |
| `database/pincode.csv` | Source CSV for the `city_pincodes` mapping table |

### city_pincodes import

The `city_pincodes` table is populated through the Flask CLI command already wired in `backend/app/commands.py`:

```bash
cd backend
flask import-pincodes
```

Use `--replace` to clear existing mappings before importing again:

```bash
cd backend
flask import-pincodes --replace
```

This command reads `database/pincode.csv`, creates any missing cities, and loads the pincode-to-city mappings used by onboarding, complaint routing, and reverse lookup.

## Schema Reference

See [docs/database/README.md](../docs/database/README.md) for the full ERD.

## Location Tables

The current schema also includes dedicated location tables and foreign keys that are required by registration, complaint routing, and municipal admin scoping:

| Table | Key relations | Purpose |
|---|---|---|
| `cities` | referenced by `users.city_id`, `complaints.city_id`, `administrator_profiles.city_id`, `city_pincodes.city_id` | Canonical city master table |
| `city_pincodes` | `city_pincodes.city_id → cities.id` | Pincode-to-city mapping imported from `database/pincode.csv` |

The detailed ERD in [docs/database/README.md](../docs/database/README.md) now includes these tables and their links to users, complaints, and administrator profiles.
