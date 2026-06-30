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
