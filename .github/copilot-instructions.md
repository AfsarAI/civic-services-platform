# GitHub Copilot Instructions — MAY2026-Team-005

This file is read automatically by GitHub Copilot in VS Code.
Every team member's Copilot will use these instructions as project context.

---

## Project

**Civic Services Platform – Pothole Reporting and Resolution System**
Course: Software Engineering | IITM Online BS Degree | Team: MAY2026-Team-005

### Tech Stack
| Layer | Technology |
|---|---|
| Backend | Python 3.13, Flask 3.1, Flask-RESTX 1.3, Flask-SQLAlchemy 3.1, Flask-Migrate 4, Flask-JWT-Extended 4.7, Marshmallow 3.23, Flask-CORS |
| Database | SQLite (dev), SQLite :memory: + StaticPool (tests) |
| Frontend | Vue 3.4, Vite 5, Pinia 2.1, Vue Router 4.3, Tailwind CSS 3.4, Axios 1.7 |
| Auth | JWT — access token 1 hr, refresh token 30 days. Identity stored as `str(user.id)`. |
| Testing | pytest, pytest-cov, pytest-flask |
| Linting | flake8 --max-line-length=120 (backend), ESLint vue3-essential (frontend) |

---

## Roles (exactly 3 — no others)
- `citizen` — submits and tracks complaints
- `field_worker` — accepts and resolves assigned complaints
- `administrator` — manages everything: complaints, users, assignments, reports

### Administrator hierarchy (subtype, NOT a 4th role)
The `administrator` role is split internally via composition — no new role was added:
- `AdministratorProfile` model/table (`admin_level`: `system` | `municipal`, `city_id`, `created_by_id`)
- **System Administrator** — created by default via `flask seed`, no `city_id`, can create/manage/disable Municipal Admins, sees all cities, global reports/user management
- **Municipal Administrator** — cannot self-register, created only by System Admin, scoped to exactly one `city_id`
- Both log in through the same `/auth/login`; JWT claims and `/auth/me` include `admin_level`, `city_id`, `city_name`
- `User` model exposes: `is_administrator`, `admin_level`, `is_system_admin`, `is_municipal_admin`, `admin_city_id`, `admin_city_name`
- Extra RBAC decorators: `require_admin_level(*levels)`, `require_system_admin`, `require_municipal_admin` (alongside `require_admin`)

---

## Baseline scope vs. added scope
- **Baseline** (`docs/project-guide/Milestone1_Report.pdf` + `docs/project-guide/Jira.csv`, 55 stories TPS-53..TPS-108): 3 user types, plain complaint CRUD/assignment/notifications/reports, no cities/map.
- **Added beyond baseline** (already implemented — treat as first-class, match existing patterns, don't re-litigate scope): Administrator hierarchy (above), `cities`/`city_pincodes` tables + pincode-first location UX, `/api/v1/locations` public namespace, mandatory photo-first pothole reporting with map pin. See `/memories/repo/drift-notes.md` for full detail if it still exists; this file is the durable source either way.

---

## Backend Architecture

### Folder layout
```
backend/
  app.py                  # entry point
  config.py               # Config / DevelopmentConfig / TestingConfig / ProductionConfig
  app/
    __init__.py           # create_app() factory
    extensions/__init__.py  # db, migrate, jwt, ma (initialised here, bound in factory)
    models/               # SQLAlchemy models (incl. City, CityPincode, AdministratorProfile)
    schemas/              # Marshmallow schemas (shared — imported by namespace schema.py)
    repositories/         # Data-access classes, e.g. AdministratorRepository — @staticmethod methods, used by services (not controllers)
    services/             # Cross-cutting services, e.g. AuditLogService.record_action(...)
    api/
      __init__.py         # Blueprint + Api, registers all namespaces
      auth/               # controller.py  service.py  schema.py
      citizen/            # includes photo upload: instance/uploads/complaints/ via secure_filename + uuid4
      administrator/
      fieldworker/
      notifications/
      reports/
      locations/          # public (no JWT) pincode/city/map lookups — controller.py + service.py, no schema.py
    utils/
      decorators.py       # RBAC + validate_body (incl. require_admin_level/require_system_admin/require_municipal_admin)
      responses.py        # standard envelope helpers
  tests/
    conftest.py           # session-scoped app + _seed_roles(); StaticPool for :memory: SQLite
    integration/
    unit/
```

### Standard API Response Envelope
**Every endpoint** returns this shape:
```json
{
  "success": true,
  "message": "Human readable string",
  "data": { ... } | null,
  "errors": null | { "field": ["error msg"] }
}
```

### Paginated Response — `data` contains items + pagination nested inside
```json
{
  "success": true,
  "message": "...",
  "data": {
    "items": [...],
    "pagination": { "page": 1, "per_page": 20, "total": 150, "pages": 8 }
  }
}
```

Use helpers from `app.utils.responses`:
```python
from app.utils.responses import success_response, error_response, paginated_response

return success_response(data, "Message.", 201)
return error_response("Something went wrong.", status_code=404)
return paginated_response(items, total, page, per_page, "List retrieved.")
```

### Request Body Validation
Use `@validate_body(SchemaClass)`. It validates JSON body via Marshmallow and injects the result as a positional arg after `self`.

```python
# No URL params
@validate_body(MySchema)
def post(self, body):
    ...

# With URL param
@validate_body(MySchema)
def put(self, body, complaint_id):   # body first, then URL kwargs
    ...
```
Returns 422 + field errors automatically on validation failure.
Returns 400 if body is not valid JSON.

### RBAC Decorators
```python
from app.utils.decorators import require_citizen, require_admin, require_field_worker

@jwt_required()       # always first
@require_citizen      # role check second (returns 403 if wrong role)
@validate_body(...)   # body validation last (if needed)
def post(self, body):
    citizen_id = int(get_jwt_identity())
```

**Critical:** All RBAC decorators return `(dict, int)` tuples — **never `jsonify()`** — because Flask-RESTX re-serialises the return value itself.

### Layer Pattern (controller → service → model)
```python
# controller.py — HTTP in/out only
@jwt_required()
@require_admin
def get(self):
    data = _svc.get_something()
    return success_response(data, "Retrieved.")

# service.py — business logic, raises ValueError for rule violations
def get_something(self) -> dict:
    item = SomeModel.query.get(id)
    if not item:
        raise ValueError("Not found.")
    return {"item": self._serialize(item)}

# In controller, map ValueError → 400/404
except ValueError as exc:
    code = 404 if "not found" in str(exc).lower() else 400
    return error_response(str(exc), status_code=code)
```

---

## Database Models & Status Constants

### Complaint statuses (`Complaint.STATUS_*`)
```
pending → assigned → in_progress → resolved → closed
      ↘ rejected   (admin can reject at any point)
```
Constants: `STATUS_PENDING`, `STATUS_ASSIGNED`, `STATUS_IN_PROGRESS`, `STATUS_RESOLVED`, `STATUS_CLOSED`, `STATUS_REJECTED`
`VALID_STATUSES` list available on the model.

### Complaint categories
`pothole`, `streetlight`, `drainage`, `garbage`, `road_damage`, `other`

### Complaint priorities
`low`, `medium`, `high`, `urgent`  ← use "urgent", NOT "critical"

### Assignment statuses (`ComplaintAssignment.STATUS_*`)
`assigned → accepted → in_progress → completed`  or  `→ rejected`

### Key business rules
- Citizen can edit/cancel only while `status == pending`
- Citizen feedback only when `status in (resolved, closed)`; one feedback per complaint (unique FK)
- Field worker accept: sets `accepted_at`; complaint → `in_progress`
- Field worker reject: complaint → `pending` (back to admin for reassignment)
- Field worker complete: sets `completed_at`; complaint stays `in_progress` (admin resolves)
- Admin resolving: set `resolved_at = datetime.now(timezone.utc)`
- Admin cannot deactivate their own account

### Schemas — which to use where
| Schema | Use for |
|---|---|
| `ComplaintCreateSchema` | Citizen submits new complaint |
| `ComplaintUpdateSchema` | Citizen edits pending complaint (**no** status/priority) |
| `AdminComplaintUpdateSchema` | Admin updates status and/or priority |
| `AssignComplaintBodySchema` | Admin assigns (body: `worker_id`, `notes`) |
| `FeedbackCreateSchema` | Citizen submits feedback (no `complaint_id` — comes from URL) |
| `FieldWorkerProgressSchema` | FW updates progress (status: `in_progress` or `rejected` only) |
| `UserUpdateSchema` | Admin updates user profile / `is_active` |

---

## Implemented Endpoints (all complete)

### Auth `/api/v1/auth` — public + JWT
- `POST /register` `POST /login` `POST /refresh` `POST /logout` `GET /me`
- `PUT /me` — any authenticated user edits own `first_name`/`last_name`/`phone` (never username/email/role)
- `POST /change-password` — any authenticated user changes own password (body: `current_password`, `new_password`, `confirm_password`)
- `POST /me/avatar` (multipart photo upload, sets `users.avatar_url`, returns updated user) `GET /me/avatar/<filename>` (serves photo, public)

### Citizen `/api/v1/citizen` — `require_citizen`
- `GET /complaints` `POST /complaints` `GET /complaints/<id>`
- `PUT /complaints/<id>` `DELETE /complaints/<id>` `POST /complaints/<id>/feedback`
- `GET /dashboard`

### Admin `/api/v1/admin` — `require_admin`
- `GET /complaints` `GET /complaints/<id>` `PUT /complaints/<id>`
- `POST /complaints/<id>/assign` `GET /field-workers`
- `POST /field-workers` `GET /field-workers/<id>` `PUT /field-workers/<id>` `DELETE /field-workers/<id>` — `require_municipal_admin` only (system admins cannot manage field workers)
- `GET /users` `GET /users/<id>` `PUT /users/<id>`
- `GET /dashboard`

**City scoping (municipal administrators only):** `GET/PUT /complaints`, `POST /complaints/<id>/assign`, and `GET /field-workers` are automatically filtered to the acting municipal administrator's own `city_id` (via `admin_user.admin_city_id`). System administrators are unscoped and see/act across all cities. A municipal administrator requesting a complaint or field worker outside their city gets 404 (not 403, to avoid leaking existence). Assigning a complaint additionally validates the field worker's `city_id` matches.

### Field Worker `/api/v1/fieldworker` — `require_field_worker`
- `GET /assignments` `GET /assignments/<id>`
- `POST /assignments/<id>/accept` `PUT /assignments/<id>` `POST /assignments/<id>/complete`
- `POST /assignments/media` (multipart photo upload, returns `evidence_url`) `GET /assignments/media/<filename>` (serves photo)
- `GET /dashboard`
- `complaint_assignments.evidence_url` (nullable) stores optional repair-completion photo, set via `POST /assignments/<id>/complete` body `{"evidence_url": "..."}` after uploading with the media endpoint above — mirrors the citizen `image_url` upload-then-reference pattern

### Reports `/api/v1/reports` — `require_admin`
- `GET /complaints/summary` `GET /complaints/by-status` `GET /complaints/by-category`
- `GET /complaints/trends?period=daily|weekly|monthly` `GET /workers/performance`

### Notifications `/api/v1/notifications` — any authenticated user
- `GET /` `GET /<id>` `PATCH /<id>/read` `PATCH /read-all` `GET /unread-count`

### Locations `/api/v1/locations` — public, no JWT required
- `GET /pincode/<pincode>` — resolve 6-digit pincode → city option(s); response has `match_count` (0/1/N) so UI can block/auto-select/prompt
- `GET /cities?query=&limit=` — city autosuggest
- `GET /pincodes?prefix=&limit=` — pincode autocomplete (min 2 digits)
- `GET /reverse-geocode?lat=&lon=` — map pin → address/pincode/city
- `GET /overview` — public landing-page stats
- `GET /complaint-pins?limit=` — public map markers from stored complaint coordinates

### Admin — Municipal Administrator management (System Admin only, `require_system_admin`)
- Register/list/manage Municipal Administrators (frontend: `/admin/municipal-administrators`, router meta `adminLevel: 'system'`)
- Writes an audit-log entry via `AuditLogService.record_action(...)` on create/update/disable

---

## Git Workflow

```
main (protected)
 └── dev (protected) ← all features merge here first
      └── feature/<rollno>-<jiraid>-short-title
```

- Always branch from `dev`
- PR: feature → dev, requires 1 approval (SM or PM)
- Jira prefix: **TPS** (e.g. TPS-70), NOT CSP
- Commit style: `feat(scope): message`, `fix(scope): message`, `test(scope): message`

---

## Running Locally

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
flask db upgrade          # apply migrations
flask seed                # create 3 roles + default System Administrator (idempotent)
flask import-pincodes     # load database/pincode.csv into city_pincodes (creates missing cities); --replace to rebuild
FLASK_APP=app.py FLASK_ENV=development flask run

# Swagger UI: http://localhost:5000/api/v1/docs
# Admin login: admin@civicservices.local / Admin@123456

# Tests
pytest                    # 18 tests, all should pass
flake8 app/ --max-line-length=120   # must be clean

# Frontend
cd frontend
npm install
npm run dev               # http://localhost:5173
```

---

## Key Gotchas

1. **JWT identity** is `str(user.id)` — always decode with `int(get_jwt_identity())`
2. **RESTX decorators** must return `(dict, int)` tuples, never `jsonify()`
3. **validate_body** injects `body` as a positional arg — signature is `def post(self, body)` or `def put(self, body, url_param)`
4. **Decorator order** on resource methods: `@jwt_required()` → `@require_*` → `@validate_body(...)`
5. **StaticPool** is set in `TestingConfig` — do not remove it or `:memory:` SQLite tests will fail
6. **DATABASE_URL** is commented out in `.env` — `config.py` computes an absolute path; never use relative `sqlite:///instance/...` in `.env`
7. **`send_notification()`** in `NotificationService` is an internal helper — call it from service methods after state changes, not from controllers
8. **`paginated_response`** nests `pagination` inside `data` — not as a sibling key
9. **Setup order matters**: `flask db upgrade` → `flask seed` → `flask import-pincodes` (pincodes import can create `cities` rows, must run after seed)
10. **Administrator is still 1 role** — never add a `system_admin`/`municipal_admin` role row; subtype lives in `AdministratorProfile.admin_level`
11. **Municipal Administrators cannot self-register** — only created by a System Administrator through the admin API (with audit logging)
12. **`city_id` is optional** in registration/creation payloads only when the given pincode resolves to exactly one city; otherwise the caller must supply it explicitly
13. **Repository classes** (`app/repositories/`) use `@staticmethod` methods and are called from services, never directly from controllers
14. **`locations` namespace has no `schema.py`** — validation there is inline (simple query-param checks), unlike other namespaces
15. **Frontend field worker portal is fully implemented** (not a placeholder): `FieldWorkerDashboard.vue` (stats + paginated/filterable assignment list) and `AssignmentDetails.vue` (accept/start-progress/reject/complete with optional evidence photo) — use these as the reference pattern (alongside `CitizenDashboard.vue`/`ComplaintDetails.vue`) for any remaining placeholder screens
16. **Field workers are created only by municipal administrators** (`require_municipal_admin`), never by system administrators and never via self-registration — `POST /admin/field-workers` always derives `city_id` from the creating administrator's own `admin_city_id`, it is never accepted from the request body
17. **`AdministratorDashboard.vue`'s complaint table and `FieldWorkers.vue` management page are fully implemented** (not placeholders) — both respect the city-scoping rules above automatically because the backend does the filtering; the frontend never needs to pass a `city_id` filter itself
18. **`Profile.vue` is shared by all 3 roles** (not per-role pages) — tabs for "Profile Details" (name/phone/avatar, username & email read-only) and "Change Password"; avatar upload follows the same upload-then-reference pattern as citizen/field-worker photos (`instance/uploads/avatars/` via `secure_filename` + `uuid4`)
