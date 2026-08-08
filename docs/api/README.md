# API Documentation

> Last reviewed: 2026-08-08

This folder contains API documentation for the Civic Services Platform REST API.

## Base URL

```
http://localhost:5000/api/v1
```

## Interactive Documentation

Swagger UI is available at:

```
http://localhost:5000/api/v1/docs
```

## Authentication

All protected endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

Obtain a token via `POST /api/v1/auth/login`.

## Namespaces

| Namespace | Base Path | Description |
|---|---|---|
| Authentication | `/api/v1/auth` | Login, register, token refresh, logout |
| Citizen | `/api/v1/citizen` | Complaint submission and tracking |
| Administrator | `/api/v1/admin` | Complaint management, user management |
| Field Worker | `/api/v1/fieldworker` | Task management, progress updates |
| Reports | `/api/v1/reports` | Statistical reports and exports |
| Notifications | `/api/v1/notifications` | User notifications |
| Locations | `/api/v1/locations` | Pincode lookup and city autosuggest |

## Assignment Notification Payload (Field Worker)

When an administrator assigns a complaint, the field worker receives a
`notification_type="complaint_assigned"` notification immediately. The
notification message includes:
- complaint ID
- assignment date and time
- complaint location
- complaint priority
- expected completion date (or "Not specified")
- administrator remarks (when provided)

Notification objects now also include `related_assignment_id` in addition to
`related_complaint_id`. Assignment notifications are idempotent per assignment
event (no duplicate notification for the same assignment record).

## Field Worker Assignment Evidence

- `POST /api/v1/fieldworker/assignments/media` — multipart photo upload (field name `photo`), returns `{ "filename": ..., "evidence_url": "/api/v1/fieldworker/assignments/media/<file>" }`.
- `GET /api/v1/fieldworker/assignments/media/<filename>` — serves the uploaded photo.
- `POST /api/v1/fieldworker/assignments/<id>/complete` — optional JSON body `{ "evidence_url": "..." }` to attach the uploaded photo when marking a task complete. Body is optional; omit it to complete without evidence.

## Administrator City Scoping

Municipal administrators (`admin_level=municipal`) are automatically scoped to their own city on:
- `GET /api/v1/admin/complaints`, `GET/PUT /api/v1/admin/complaints/<id>`, `POST /api/v1/admin/complaints/<id>/assign`
- `GET /api/v1/admin/field-workers`

System administrators (`admin_level=system`) are unscoped and see every city. Requesting a complaint or field worker outside a municipal administrator's own city returns `404`.

## Field Worker Management (Municipal Administrator only)

- `POST /api/v1/admin/field-workers` — create a field worker. `city_id` is never accepted in the body; it is always the creating administrator's own city. Body: `username`, `email`, `password`, `confirm_password`, `first_name`, `last_name`, `phone` (optional).
- `GET /api/v1/admin/field-workers/<id>` — view one field worker (system admins can view any; municipal admins only their own city's).
- `PUT /api/v1/admin/field-workers/<id>` — edit profile fields (`first_name`, `last_name`, `email`, `phone`) and/or `is_active` (activate/deactivate), and/or reset the password (`password` + `confirm_password`). `email` conflicts return `409`.
- `DELETE /api/v1/admin/field-workers/<id>` — shorthand for deactivating.
- `GET /api/v1/admin/field-workers?is_active=true|false` — list/filter; omit `is_active` to see both active and inactive workers.

## User Management, Password Reset & Email Update (Milestone 4)

- `GET /api/v1/admin/users` and `GET/PUT /api/v1/admin/users/<id>` are no
  longer system-admin-only. **System administrators** are unscoped (any
  role). **Municipal administrators** may also call these, but the `role`
  filter is forced server-side to `citizen` and results are scoped to their
  own `city_id` — they cannot see or edit field workers, other municipal
  admins, or citizens outside their city (`404` if attempted).
- `PUT /api/v1/admin/users/<id>`, `PUT /api/v1/admin/field-workers/<id>`, and
  `PUT /api/v1/admin/municipal-administrators/<id>` all accept optional
  `email` and `password`/`confirm_password` fields on top of their existing
  profile fields — this is how an administrator resets a forgotten password
  or corrects an email for the accounts they manage, with no SMTP/email
  infrastructure required. `confirm_password` mismatches return `422`; a
  duplicate `email` returns `409`.
- `GET /api/v1/reports/feedback/summary` — citizen feedback summary (average
  rating, star distribution, recent comments), scoped like the other report
  endpoints. See `docs/milestone4/openapi-with-user-stories.yaml` for the
  full request/response schema.

System administrators cannot create, edit, or deactivate field workers — these endpoints require `admin_level=municipal` (`require_municipal_admin`).

## System Settings (System Administrator only)

- `GET /api/v1/admin/settings` / `PUT /api/v1/admin/settings` — singleton platform configuration: `site_name`, `support_email`, `maintenance_mode`, `notify_on_status_change`, `default_complaint_priority`.
- `maintenance_mode` takes effect immediately on the next login attempt (blocks citizen/field worker logins with a clear message; administrators are unaffected).
- `notify_on_status_change` takes effect immediately on the next assignment/accept/reject/resolve/close action (suppresses all automatic notification sends when `false`).
- Every update writes an audit-log entry (`action="system_settings_updated"`).

## Self-Service Profile (all authenticated roles)

- `PUT /api/v1/auth/me` — update own `first_name`, `last_name`, `phone`. Username, email, and role are never editable here.
- `POST /api/v1/auth/change-password` — body `current_password`, `new_password`, `confirm_password`. Rejects if the current password is wrong, the new password fails strength rules, or confirm doesn't match.
- `POST /api/v1/auth/me/avatar` — multipart photo upload (field name `photo`), stores the file and immediately sets `users.avatar_url`, returns the updated user.
- `GET /api/v1/auth/me/avatar/<filename>` — serves the uploaded photo (public, unguessable UUID filename).

## Location Lookup Endpoints

- `GET /api/v1/locations/pincode/<pincode>`
  - Resolves a 6-digit pincode into one or more city options.
  - Returns `match_count = 0/1/N` so UI can handle no-match, auto-select, or user-choice flow.
- `GET /api/v1/locations/cities?query=<text>&limit=<n>`
  - Returns active city suggestions for autosuggest controls.

## Registration Payload Update

Citizen registration now requires pincode-backed location fields:

```json
{
  "username": "citizen1",
  "email": "citizen@example.com",
  "password": "Secure@123",
  "first_name": "Citizen",
  "last_name": "User",
  "pincode": "226001",
  "city_id": 1
}
```

`city_id` is optional only when pincode maps to exactly one city.

## Response Format

All responses follow this envelope structure:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... },
  "errors": null
}
```

## HTTP Status Codes

| Code | Meaning |
|---|---|
| `200` | OK |
| `201` | Created |
| `400` | Bad Request — invalid JSON or business rule violation |
| `401` | Unauthorised — missing or invalid JWT token |
| `403` | Forbidden — valid token, insufficient role |
| `404` | Not Found |
| `409` | Conflict — duplicate resource (e.g. email already registered) |
| `422` | Unprocessable Entity — Marshmallow validation failed (field-level errors in `errors` key) |
| `500` | Internal Server Error |

## Documentation Backlog

- [ ] Export Swagger JSON to this folder
- [ ] Add endpoint-level request/response examples
- [ ] Document rate limiting policy
