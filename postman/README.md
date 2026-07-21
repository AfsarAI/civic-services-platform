# Postman Collection — Civic Services Platform

> Last reviewed: 2026-07-21

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
| Citizen | Submit, view, and track complaints |
| Administrator | Manage complaints, assign workers |
| Field Worker | View tasks, update progress |
| Reports | Statistics and analytics |
| Notifications | View and manage notifications |
| Locations | Pincode and city lookup endpoints |
