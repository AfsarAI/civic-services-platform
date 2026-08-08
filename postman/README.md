# Postman Collection — Civic Services Platform

> Last reviewed: 2026-08-08

This folder contains the Postman API collection for testing the Civic Services Platform REST API.

## Import

1. Open **Postman**
2. Click **Import**
3. Select `Civic-Services-Platform.postman_collection.json`

## Environment Setup

Set the following **Collection Variables** in Postman:

| Variable | Value |
|---|---|
| `base_url` | `http://localhost:5000/api/v1` |
| `access_token` | *(auto-filled by Login request)* |
| `refresh_token` | *(auto-filled by Login request)* |

## Usage

1. Run the **Authentication / Login** request first — the token is automatically saved as a collection variable.
2. All subsequent requests use `{{access_token}}` for authorisation.

## Collections

| Folder | Description |
|---|---|
| Authentication | Register, Login, Refresh, Logout, Me |
| Citizen | Submit, view, and track complaints; check for nearby possible-duplicate reports before submitting |
| Administrator | Manage complaints, assign workers, manage users/field workers/municipal administrators, reset a password or update an email for any account they're scoped to, and review/mark duplicate complaints |
| Field Worker | View tasks, update progress |
| Reports | Statistics, analytics, feedback summary, and CSV export |
| Notifications | View and manage notifications |
| Locations | Public (no auth) pincode lookup, city/pincode autosuggest, reverse-geocode, and map data |
| System Settings | Platform-wide configuration (System Administrator only), including the duplicate-detection radius |

## Password Reset & Email Update

The **Administrator** folder includes "Reset User Password", "Update User Email",
"Reset Field Worker Password", and "Reset Municipal Administrator Password"
requests. These all use `PUT` with an optional `password`/`confirm_password`
and/or `email` field on top of the existing profile fields — no separate
endpoint was added. A System Administrator can reset/update any user; a
Municipal Administrator is limited to their own city's Field Workers and
Citizens. See `docs/milestone4/openapi-with-user-stories.yaml` for full
request/response documentation.

## Duplicate Pothole Detection

The **Citizen** folder's "Check Nearby Duplicates" request is an advisory,
never-blocking check the report form calls before submission. The
**Administrator** folder's "Get Duplicate Candidates" and "Mark Complaint as
Duplicate" requests let an admin review nearby open complaints and
explicitly link one as a duplicate of another (reuses the existing
`rejected` status transition and notifies the citizen). The detection radius
is configurable via the **System Settings** folder's "Update System Settings"
request (`duplicate_detection_radius_meters`, default 50m).
