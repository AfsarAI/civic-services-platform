# Database Documentation

This folder contains the database schema, ERD, and migration history for the Civic Services Platform.

## Entity Relationship Diagram

```
┌──────────┐       ┌──────────────────┐       ┌────────────────────┐
│   Role   │       │      User        │       │     Complaint      │
│──────────│       │──────────────────│       │────────────────────│
│ id (PK)  │◄──────│ id (PK)          │──────►│ id (PK)            │
│ name     │       │ username         │       │ title              │
│ description│     │ email            │       │ description        │
└──────────┘       │ password_hash    │       │ category           │
                   │ role_id (FK)     │       │ status             │
                   │ is_active        │       │ latitude           │
                   │ created_at       │       │ longitude          │
                   │ updated_at       │       │ citizen_id (FK)    │
                   └──────────────────┘       │ created_at         │
                                              │ updated_at         │
                                              └────────────────────┘
                                                        │
                                              ┌─────────▼──────────┐
                                              │ ComplaintAssignment │
                                              │────────────────────│
                                              │ id (PK)             │
                                              │ complaint_id (FK)   │
                                              │ worker_id (FK)      │
                                              │ assigned_by (FK)    │
                                              │ assigned_at         │
                                              │ status              │
                                              └────────────────────┘
```

## Models

| Model | Table | Description |
|---|---|---|
| `Role` | `roles` | User roles (Citizen, Administrator, Field Worker) |
| `User` | `users` | Platform users with role association |
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

## TODO

- [ ] Add full ERD image (use draw.io or dbdiagram.io)
- [ ] Document all column constraints
- [ ] Add index documentation
