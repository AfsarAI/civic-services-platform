# Deployment

> Last reviewed: 2026-07-21

This folder contains deployment configuration for the Civic Services Platform.

## Deployment Options

| Environment | Status |
|---|---|
| Local Development | Ready (see root README) |
| Docker Compose | Planned |
| Production | Planned |

## Local Development

Follow the instructions in the root [README.md](../README.md).

## Docker (Planned)

A `docker-compose.yml` will be added here for containerised deployment.

## Environment Variables

Always use environment-specific `.env` files — **never commit secrets**.

Production secrets should be managed via a secrets manager (e.g. GitHub Actions Secrets, AWS Secrets Manager).

## Deployment Backlog

- [ ] Create `Dockerfile` for backend
- [ ] Create `Dockerfile` for frontend
- [ ] Create `docker-compose.yml` for local + production
- [ ] Add Nginx reverse proxy configuration
- [ ] Document production deployment steps
