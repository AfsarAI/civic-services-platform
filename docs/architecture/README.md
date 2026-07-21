# Architecture Documentation

> Last reviewed: 2026-07-21

This folder contains architectural decision records (ADRs) and system design diagrams for the Civic Services Platform.

## Contents

| File | Description |
|---|---|
| `README.md` | Primary architecture overview and decisions |
| `diagrams/` | Source diagrams (`.drawio`) for architecture/database artifacts |

Planned additions:
- `adr/` directory for architecture decision records
- dedicated context/container sequence diagrams

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Client Browser                      │
│               Vue 3 SPA (Vite + Tailwind)               │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS / REST
┌───────────────────────▼─────────────────────────────────┐
│                    Flask REST API                        │
│            Flask-RESTX  │  Flask-JWT-Extended            │
│            Blueprints   │  Flask-CORS                   │
└───────────────────────┬─────────────────────────────────┘
                        │ SQLAlchemy ORM
┌───────────────────────▼─────────────────────────────────┐
│                    SQLite Database                       │
│              (Alembic / Flask-Migrate)                  │
└─────────────────────────────────────────────────────────┘
```

## Technology Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Frontend Framework | Vue 3 | Composition API, ecosystem maturity |
| Backend Framework | Flask | Lightweight, extensible, Pythonic |
| API Style | REST + Swagger | Industry standard, self-documenting |
| Authentication | JWT | Stateless, scalable |
| Database | SQLite | Simple dev setup, upgradeable |
| State Management | Pinia | Official Vue recommendation |

## Administrator Hierarchy Design

The project keeps exactly three coarse application roles:
- `citizen`
- `administrator`
- `field_worker`

Administrator subtype separation is implemented with composition, not a new role:
- `users` holds identity and coarse role
- `administrator_profiles` holds subtype and scope
- `cities` holds the municipal boundary

Why this design was chosen:
- keeps the existing login flow unchanged
- avoids introducing a new `SystemAdmin` role
- keeps admin-only state out of the base `roles` table
- scales better than a single boolean such as `is_system_admin`

Subtype rules:
- `system` administrators have no city and can manage municipal admins globally
- `municipal` administrators must reference exactly one city
- system-only permissions are enforced in backend decorators and controllers

## Class UML Diagram

Core backend domain classes and their primary relationships:

```mermaid
classDiagram
        direction LR

        class Role {
            +int id
            +string name
            +string description
        }

        class User {
            +int id
            +string username
            +string email
            +string first_name
            +string last_name
            +bool is_active
            +int role_id
            +int city_id
            +string pincode
        }

        class AdministratorProfile {
            +int id
            +int user_id
            +string admin_level
            +int city_id
            +int created_by_id
        }

        class City {
            +int id
            +string name
            +string state
            +bool is_active
        }

        class CityPincode {
            +int id
            +string pincode
            +int city_id
            +string area_name
        }

        class Complaint {
            +int id
            +string title
            +string category
            +string status
            +string priority
            +int citizen_id
            +int city_id
        }

        class ComplaintAssignment {
            +int id
            +int complaint_id
            +int worker_id
            +int assigned_by_id
            +string status
            +datetime completed_at
        }

        class Feedback {
            +int id
            +int complaint_id
            +int citizen_id
            +int rating
        }

        class Notification {
            +int id
            +int user_id
            +string notification_type
            +bool is_read
            +int related_complaint_id
        }

        class AuditLog {
            +int id
            +int user_id
            +string action
            +string resource_type
            +int resource_id
        }

        class SystemSetting {
            +int id
            +string site_name
            +bool maintenance_mode
            +bool notify_on_status_change
            +int updated_by_id
        }

        Role "1" --> "*" User : assigns role
        City "1" --> "*" User : scoped users
        User "1" --> "0..1" AdministratorProfile : admin profile
        City "1" --> "*" AdministratorProfile : municipal scope
        User "1" --> "*" AdministratorProfile : created by

        City "1" --> "*" CityPincode : pincode mappings

        User "1" --> "*" Complaint : submits
        City "1" --> "*" Complaint : located in

        Complaint "1" --> "*" ComplaintAssignment : assignments
        User "1" --> "*" ComplaintAssignment : worker
        User "1" --> "*" ComplaintAssignment : assigned by

        Complaint "1" --> "0..1" Feedback : feedback
        User "1" --> "*" Feedback : gives

        User "1" --> "*" Notification : receives
        Complaint "1" --> "*" Notification : related

        User "1" --> "*" AuditLog : actor
        User "1" --> "*" SystemSetting : updated by
```

## Architecture Backlog

- [ ] Add C4 Context diagram
- [ ] Add C4 Container diagram
- [ ] Add sequence diagrams for key flows
- [ ] Document deployment architecture
