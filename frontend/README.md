# Frontend — Civic Services Platform

> Last reviewed: 2026-07-21

Vue 3 SPA for the Civic Services Platform.

## Quick Start

```bash
npm install
cp .env.example .env
npm run dev
```

Visit `http://localhost:5173`.

## Structure

```
src/
├── assets/          Static assets (images, fonts)
├── components/      Reusable components (Navbar, Sidebar, Footer)
├── layouts/         Page layouts (DefaultLayout, AuthLayout)
├── pages/           Route-level page components
│   ├── citizen/
│   ├── administrator/
│   └── fieldworker/
├── router/          Vue Router configuration
├── stores/          Pinia state stores (auth, complaint)
├── services/        Axios API service layer
├── styles/          Global CSS (Tailwind)
└── utils/           Utility helpers
```

## Build

```bash
npm run build
```

Output is in `dist/`.

## Authentication Session Flow

- Login API integration is handled by `src/services/auth.service.js` (`AuthService` class).
- Session state is managed in `src/stores/auth.js`:
  - `login`, `logout`, `fetchCurrentUser`, `hydrateSession`
  - localStorage keys: `access_token`, `refresh_token`, `user`
- Role-based redirection after login:
  - Administrator → `/admin/dashboard`
  - Citizen → `/citizen/dashboard`
  - Field Worker → `/fieldworker/dashboard`
- Router-level guards in `src/router/index.js` enforce auth + role authorization.
- Registration and municipal-admin onboarding call `GET /locations/pincode/<pincode>` for city resolution.
