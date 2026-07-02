# UI / UX Documentation

This folder contains UI design documentation, wireframes, and component guidelines for the Civic Services Platform frontend.

## Pages

| Page | Route | Role |
|---|---|---|
| Login | `/login` | All |
| Dashboard | `/dashboard` | All (redirects by role) |
| Citizen Dashboard | `/citizen/dashboard` | Citizen |
| Report Complaint | `/citizen/report` | Citizen |
| Track Complaint | `/citizen/track` | Citizen |
| Complaint Details | `/citizen/complaints/:id` | Citizen |
| Administrator Dashboard | `/admin/dashboard` | Administrator |
| Reports | `/admin/reports` | Administrator |
| Field Worker Dashboard | `/fieldworker/dashboard` | Field Worker |
| Profile | `/profile` | All |
| Not Found | `/:pathMatch(.*)` | All |

## Layout Components

| Component | Description |
|---|---|
| `DefaultLayout` | Main layout with Navbar, Sidebar, Footer |
| `AuthLayout` | Minimal layout for Login page |
| `Navbar` | Top navigation bar |
| `Sidebar` | Role-aware side navigation |
| `Footer` | Application footer |

## Authentication UX Flow (Implemented)

1. `/login` is publicly accessible through `AuthLayout`.
2. Credentials are submitted from `Login.vue` to the auth store action `login(email, password)`.
3. On successful authentication:
   - `administrator` → `/admin/dashboard`
   - `citizen` → `/citizen/dashboard`
   - `field_worker` → `/fieldworker/dashboard`
4. Invalid credentials render inline error feedback in the login form.
5. Route guards enforce:
   - Guest-only access to `/login`
   - Authenticated-only access for protected routes
   - Role-specific access for admin/citizen/field-worker pages

## Design System

- **CSS Framework:** Tailwind CSS v3
- **Color Palette:** To be defined in `tailwind.config.js`
- **Typography:** To be defined
- **Icons:** To be decided (e.g. Heroicons / Lucide)

## TODO

- [ ] Add Figma/wireframe links
- [ ] Document component library
- [ ] Add responsive breakpoint guidelines
- [ ] Define color tokens
