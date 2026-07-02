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

### Admin Login Flow (Implemented)

1. `POST /api/v1/auth/login` validates credentials and returns `access_token`, `refresh_token`, and `user`.
2. Frontend creates an authenticated session by storing:
   - `access_token`
   - `refresh_token`
   - `user`
3. Administrator users are redirected to `/admin/dashboard` after successful login.
4. Admin APIs enforce:
   - coarse role checks with `require_admin`
   - subtype checks with `require_system_admin` where required
5. Expired access tokens are renewed through `POST /api/v1/auth/refresh`.
6. `POST /api/v1/auth/logout` ends the session client-side by clearing stored tokens and profile.

### Administrator Hierarchy Payload

The login contract is unchanged: both admin subtypes still return `role: "administrator"`.

Additional fields now returned in `user` and JWT claims:
- `admin_level`: `system` or `municipal`
- `city_id`: nullable, present for municipal administrators
- `city_name`: nullable, present for municipal administrators

### New System Administrator Endpoints

- `GET /api/v1/admin/cities`
- `GET /api/v1/admin/municipal-administrators`
- `POST /api/v1/admin/municipal-administrators`
- `GET /api/v1/admin/municipal-administrators/<user_id>`
- `PUT /api/v1/admin/municipal-administrators/<user_id>`

These endpoints are restricted to the System Administrator subtype.

## Namespaces

| Namespace | Base Path | Description |
|---|---|---|
| Authentication | `/api/v1/auth` | Login, register, token refresh, logout |
| Citizen | `/api/v1/citizen` | Complaint submission and tracking |
| Administrator | `/api/v1/admin` | Complaint management, user management |
| Field Worker | `/api/v1/fieldworker` | Task management, progress updates |
| Reports | `/api/v1/reports` | Statistical reports and exports |
| Notifications | `/api/v1/notifications` | User notifications |

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
