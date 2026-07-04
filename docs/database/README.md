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
                │ is_active        │    │ image_url                 │
                │ created_at       │    │ citizen_id (FK → users)   │
                │ updated_at       │    │ resolved_at               │
                └────────┬─────────┘    │ created_at / updated_at   │
                         │              └──────────────┬────────────┘
                         │                             │
         ┌───────────────▼───────────────┐             │
         │     AdministratorProfile      │             │
         │───────────────────────────────│             │
         │ id (PK)                       │             │
         │ user_id (FK → users, unique)  │             │
         │ admin_level (system/municipal)│             │
         │ city_id (FK → cities, null for│             │
         │   system admin only)          │             │
         │ created_by_id (FK → users)    │             │
         └───────────────┬───────────────┘             │
                         │                             │
                ┌────────▼────────┐                    │
                │      City       │                    │
                │─────────────────│                    │
                │ id (PK)         │                    │
                │ name            │                    │
                │ state           │                    │
                │ is_active       │                    │
                └─────────────────┘                    │
                                                       │
              ┌────────────────────────────────────────┤
              │                                        │
┌─────────────▼──────────┐        ┌───────────────────▼──┐
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
| `City` | `cities` | Administrative city used for municipal administrator assignment |
| `AdministratorProfile` | `administrator_profiles` | Administrator subtype (`system` or `municipal`) and city scope |
| `Complaint` | `complaints` | Civic complaints submitted by citizens |
| `ComplaintAssignment` | `complaint_assignments` | Assignment of complaints to field workers |
| `Notification` | `notifications` | System notifications to users |
| `Feedback` | `feedback` | Citizen feedback on resolved complaints |
| `AuditLog` | `audit_logs` | System audit trail |

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

## Administrator Hierarchy Notes

- The `roles` table still contains only `citizen`, `administrator`, and `field_worker`.
- `administrator_profiles` is the authoritative source for distinguishing System and Municipal Administrators.
- Municipal administrators must reference exactly one row in `cities`.
- System administrators must not reference a city.

## TODO

- [ ] Add full ERD image (use draw.io or dbdiagram.io)
- [ ] Document all column constraints
- [ ] Add index documentation
