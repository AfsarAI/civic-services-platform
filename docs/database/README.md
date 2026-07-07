# Database Documentation

This folder contains the database schema, ERD, and migration history for the Civic Services Platform.

## Entity Relationship Diagram

```
┌──────────┐    ┌──────────────────┐    ┌───────────────────────────┐
│   Role   │    │      User        │    │        Complaint          │
│──────────│    │──────────────────│    │───────────────────────────│
│ id (PK)  │◄───│ id (PK)          │───►│ id (PK)                   │
│ name     │    │ username         │    │ title                     │
│ description│  │ email            │    │ description               │
└──────────┘    │ password_hash    │    │ category                  │
                │ first_name       │    │ status (pending→closed)   │
                │ last_name        │    │ priority (low/med/high)   │
                │ phone            │    │ latitude / longitude      │
                │ role_id (FK)     │    │ address                   │
                │ city_id (FK) ────────►│ city_id (FK)              │
                │ pincode          │    │ pincode                   │
                │ is_active        │    │ image_url                 │
                │ created_at       │    │ citizen_id (FK → users)   │
                │ updated_at       │    │ resolved_at               │
                └────────┬─────────┘    │ created_at / updated_at   │
                         │              └──────────────┬────────────┘
                         │                             │
                         │                             │
                ┌────────▼──────────┐         ┌────────▼───────────┐
                │       City        │◄────────│    CityPincode     │
                │───────────────────│         │────────────────────│
                │ id (PK)           │         │ id (PK)            │
                │ name              │         │ pincode            │
                │ state             │         │ city_id (FK)       │
                │ is_active         │         │ area_name          │
                │ created_at        │         │ district           │
                │ updated_at        │         │ state              │
                └────────┬──────────┘         │ is_active          │
                         │                    │ created_at         │
                         │                    │ updated_at         │
                         │                    └────────────────────┘
                         │
         ┌───────────────▼────────────────┐
         │      AdministratorProfile      │
         │────────────────────────────────│
         │ id (PK)                        │
         │ user_id (FK → users)           │
         │ admin_level (system/municipal) │
         │ city_id (FK → cities)          │
         │ created_by_id (FK → users)     │
         │ created_at / updated_at        │
         └────────────────────────────────┘

┌────────────────────────┐        ┌───────────────────────┐
│   ComplaintAssignment  │        │       Feedback        │
│────────────────────────│        │───────────────────────│
│ id (PK)                │        │ id (PK)               │
│ complaint_id (FK)      │        │ complaint_id (FK)     │
│ worker_id (FK → users) │        │ citizen_id (FK)       │
│ assigned_by (FK → user)│        │ rating (1–5)          │
│ assigned_at            │        │ comment               │
│ accepted_at            │        │ submitted_at          │
└────────────────────────┘        └───────────────────────┘

┌───────────────────────────┐     ┌─────────────────────────┐
│       Notification        │     │        AuditLog         │
│───────────────────────────│     │─────────────────────────│
│ id (PK)                   │     │ id (PK)                 │
│ user_id (FK → users)      │     │ user_id (FK)            │
│ message                   │     │ action                  │
│ type                      │     │ entity_type             │
│ is_read                   │     │ entity_id               │
│ created_at                │     │ timestamp               │
└───────────────────────────┘     └─────────────────────────┘
```

### Location relationship summary

- `users.city_id → cities.id` stores the citizen's or worker's home city context.
- `complaints.city_id → cities.id` stores the routing snapshot used when the complaint was filed.
- `administrator_profiles.city_id → cities.id` scopes municipal administrators to a single city.
- `city_pincodes.city_id → cities.id` maps one pincode to one or more city records.

## Complaint Status Flow

```
pending → assigned → in_progress → resolved → closed
                                 ↘ rejected  (admin can reject at any point)
```


## Models

| Model | Table | Description |
|---|---|---|
| `Role` | `roles` | User roles (Citizen, Administrator, Field Worker) |
| `User` | `users` | Platform users with role association |
| `City` | `cities` | Canonical city master used by onboarding, routing, and admin scope |
| `AdministratorProfile` | `administrator_profiles` | Administrator subtype and municipal city scope |
| `Complaint` | `complaints` | Civic complaints submitted by citizens |
| `CityPincode` | `city_pincodes` | Master mapping of pincode to one/more cities |
| `ComplaintAssignment` | `complaint_assignments` | Assignment of complaints to field workers |
| `Notification` | `notifications` | System notifications to users |
| `Feedback` | `feedback` | Citizen feedback on resolved complaints |
| `AuditLog` | `audit_logs` | System audit trail |

## Location Mapping Additions

- `users.city_id`, `users.pincode`: stores citizen/admin onboarding location.
- `complaints.city_id`, `complaints.pincode`: persisted routing snapshot at complaint creation time.
- `city_pincodes` indexes:
    - `ix_city_pincodes_pincode`
    - `ix_city_pincodes_city_id`

This makes runtime lookups DB-native and avoids querying CSV files in request paths.

## Migrations

Managed via **Alembic** through **Flask-Migrate**.

```bash
# Apply all pending migrations
flask db upgrade

# Roll back last migration
flask db downgrade

# Show migration history
flask db history
```

## Seeding Reference

The project uses two separate seed/import steps:

1. `flask seed` creates the three base roles and the default system administrator.
2. `flask import-pincodes` loads `city_pincodes` from `database/pincode.csv` and creates any missing `cities` rows.

Recommended setup order after configuring the backend:

```bash
cd backend
flask db upgrade
flask seed
flask import-pincodes
```

Use `flask import-pincodes --replace` if you need to rebuild the mapping table from the CSV.

## TODO

- [ ] Add full ERD image (use draw.io or dbdiagram.io)
- [ ] Document all column constraints
- [ ] Add index documentation
