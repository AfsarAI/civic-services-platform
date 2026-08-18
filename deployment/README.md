# Deployment

> Last reviewed: 2026-08-18

Chosen architecture for this project:

| Component | Where | Why |
|---|---|---|
| Frontend (Vue 3 SPA) | **Azure App Service** (same app as the API) | Repo is private — GitHub Pages free tier only serves Pages for public repos |
| Backend API (Flask) | **Azure App Service (Linux, Python)** | Free/Basic tier, runs gunicorn directly, easy env-var config |
| Database | **Azure Database for PostgreSQL — Flexible Server** | Managed Postgres, Burstable/free-eligible tier via Azure for Students |

Frontend and backend are deployed **together as one App Service**: the CI
workflow builds `frontend/dist` and copies it into `backend/static_frontend`;
Flask serves it from the same origin as `/api/v1/...` (see
`_register_frontend()` in `backend/app/__init__.py`). This avoids needing a
public repo/GitHub Pages and avoids CORS entirely (same origin).

CI (lint/test on every PR) already exists in `.github/workflows/backend-ci.yml`
and `frontend-ci.yml`. Deployment runs on push to `main` via
`.github/workflows/deploy-backend.yml`.

---

## 1. Azure Database for PostgreSQL

1. Create **Azure Database for PostgreSQL – Flexible Server** (Burstable B1ms is
   enough; enable "Free tier" if your subscription offers it).
2. Networking: allow **"Allow public access from any Azure service within Azure to
   this server"** so App Service can reach it. Also add your own IP so you can run
   migrations locally.
3. Create a database, e.g. `civic_db`.
4. Build the connection string (SSL is mandatory on Flexible Server). **If your
   password contains any of `@ : / % ?` etc., percent-encode them** — an
   unescaped `@` in particular breaks host parsing (`@` is otherwise the
   userinfo/host separator):
   ```
   postgresql://<user>:<url-encoded-password>@<server-name>.postgres.database.azure.com:5432/civic_db?sslmode=require
   ```
5. From your machine, point the backend at it and initialise the schema **once**:
   ```bash
   cd backend
   export DATABASE_URL="postgresql://...?sslmode=require"
   export FLASK_APP=app.py
   flask db upgrade
   flask seed
   flask import-pincodes
   ```
   Re-run `flask db upgrade` after every migration you add — it's idempotent.

## 2. Single Azure App Service (API + frontend)

1. Create an **App Service** → Linux, **Python 3.13** runtime, Basic (B1) or Free (F1) plan.
2. **Configuration → Application settings**, add:
   | Name | Value |
   |---|---|
   | `FLASK_ENV` | `production` |
   | `SECRET_KEY` | a long random string |
   | `JWT_SECRET_KEY` | a different long random string |
   | `DATABASE_URL` | the (URL-encoded) Postgres connection string from step 1 |
   | `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |

   `CORS_ORIGINS` is no longer required for the app to function (frontend and
   API now share one origin) — only set it if you also want to hit the API
   directly from a separately-hosted client (e.g. Postman's browser app).
3. **Configuration → General settings → Startup Command:**
   ```
   gunicorn --bind=0.0.0.0 --timeout 600 app:app
   ```
4. **Deployment Center → GitHub Actions** (or download the *Publish Profile*
   manually) and add these to **repo Settings → Secrets and variables → Actions**:
   - Secret `AZURE_WEBAPP_PUBLISH_PROFILE` — full contents of the downloaded publish profile XML
   - Variable `AZURE_WEBAPP_NAME` — the App Service name
5. Push to `main` touching `backend/**` or `frontend/**` (or run the workflow
   manually) to deploy — `deploy-backend.yml` builds both and deploys them together.
6. Verify:
   - `https://<app-name>.azurewebsites.net/api/v1/docs` → Swagger UI
   - `https://<app-name>.azurewebsites.net/` → the Vue app

**Uploaded photos caveat:** `instance/uploads/` is written to local disk
(`/home/site/wwwroot/instance/uploads` on App Service). Azure App Service persists
`/home` across restarts on a *single* instance, but this breaks if you ever scale
out to multiple instances. Fine for a single-instance college deployment; not a
production-grade file store (would need Azure Blob Storage for that).

## 3. Post-deploy checklist

- [ ] Swagger UI reachable at the Azure URL
- [ ] `flask db upgrade` + `flask seed` + `flask import-pincodes` run against the Azure DB
- [ ] The Vue app loads at the Azure root URL and login succeeds
- [ ] Refreshing a deep link (e.g. `/citizen/dashboard`) doesn't 404 (handled
      server-side by `_register_frontend()`'s catch-all route)
- [ ] Photo upload + retrieval works end-to-end
- [ ] Rotate `SECRET_KEY`/`JWT_SECRET_KEY`/DB password if they were ever pasted
      into a chat, doc, or ticket — treat as compromised

## Environment variables — never commit secrets

Always use environment-specific `.env` files locally; in CI/production use GitHub
Actions Secrets/Variables and Azure App Service Application Settings, as above.

## Local development

Follow the instructions in the root [README.md](../README.md). Locally the
frontend still runs separately via `npm run dev` (port 5173) against the Flask
API (port 5000) — `_register_frontend()` only activates when
`backend/static_frontend/` exists, which it doesn't in a normal dev checkout.

## Possible future improvements (not required for the college submission)

- Docker Compose for local parity with production
- Azure Blob Storage for uploaded photos (removes the single-instance constraint)
- Make the repo public and split back out to GitHub Pages + a separate API
  origin, if ever desired (would need `CORS_ORIGINS` set again)
