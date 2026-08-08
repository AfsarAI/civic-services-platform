# User Manual

> Last reviewed: 2026-08-08

This folder contains end-user documentation for the Civic Services Platform.

## Roles

The platform has exactly **3 user roles** (per Milestone 1 Report):

### Citizen
- Register an account and log in
- Submit a pothole complaint with a photo, map pin, and location details
- Track the status of submitted complaints in real time
- Edit or cancel a complaint (only while status is `pending` and not yet assigned)
- Provide feedback and a rating after a complaint is resolved
- View full complaint history

### Administrator

The platform still uses one administrator login flow, but there are now two administrator levels.

#### System Administrator
- Exists by default after backend seeding
- Logs in through the normal admin login form
- Creates Municipal Administrators
- Manages and disables Municipal Administrators
- Views all cities
- Accesses global reports and user-management features
- Uses the `Manage Municipal Administrators` page from the dashboard/sidebar to register city-wise administrators
- Uses the `Citizens` page (`/admin/citizens`) to view any citizen, edit their name/last name/email/phone, or reset their password if they've forgotten it
- Can reset the password or update the email of any Municipal Administrator or Field Worker as well, if they're locked out or need a correction

#### Municipal Administrator
- Cannot self-register
- Receives credentials from the System Administrator
- Belongs to exactly one city
- Logs in through the same admin login form
- Sees the shared administrator dashboard with city-scoped identity information
- Uses the `Citizens` page to view, edit, and reset the password of Citizens registered in their own city only (citizens in other cities are not visible)
- Uses the `Field Workers` page to reset a Field Worker's password or update their email/details, in addition to creating and deactivating accounts

### Field Worker
- Log in with field worker credentials
- View all complaints assigned to them
- Accept an assigned complaint
- Update repair progress (`in_progress`)
- Mark a complaint as complete and upload photographic evidence
- View work history

## Complaint Lifecycle

```
pending  →  assigned  →  in_progress  →  resolved  →  closed
   ↘ cancelled (citizen can cancel only while pending)
   ↘ rejected (administrator can reject before terminal closure)
```

- Citizen can **edit** or **cancel** only while status = `pending`
- Field worker accepts work and updates assignment progress, then marks repair complete with optional evidence upload
- Complaint status remains `in_progress` after worker completion until an administrator verifies it
- Administrator verifies and moves complaint to `resolved`, then finally to `closed`
- Administrator can reject only non-terminal complaints (`pending`, `assigned`, `in_progress`)

## Forgotten Password

There is no citizen-facing self-service "forgot password" flow (it would
require email/SMTP infrastructure this project does not have). Instead:

- A **Citizen** who forgets their password should contact a System
  Administrator or their city's Municipal Administrator, who can reset it
  from the `Citizens` page.
- A **Field Worker** who forgets their password should contact their
  Municipal Administrator, who can reset it from the `Field Workers` page.
- A **Municipal Administrator** who forgets their password should contact
  the System Administrator, who can reset it from the `Municipal
  Administrators` page.

## User Manual Backlog

- [ ] Add step-by-step user guides with screenshots
- [ ] Add FAQ section
- [ ] Add video walkthroughs
