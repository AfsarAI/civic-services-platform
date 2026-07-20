# API Documentation

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
- `PUT /api/v1/admin/field-workers/<id>` — edit profile fields and/or `is_active` (activate/deactivate).
- `DELETE /api/v1/admin/field-workers/<id>` — shorthand for deactivating.
- `GET /api/v1/admin/field-workers?is_active=true|false` — list/filter; omit `is_active` to see both active and inactive workers.

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

## TODO

- [ ] Export Swagger JSON to this folder
- [ ] Add endpoint-level request/response examples
- [ ] Document rate limiting policy
