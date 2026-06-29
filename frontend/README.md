# Frontend — Civic Services Platform

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
