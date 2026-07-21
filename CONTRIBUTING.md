# Contributing to Civic Services Platform

> Last reviewed: 2026-07-21

Thank you for contributing! This document outlines the contribution guidelines for this Scrum project.

---

## Code of Conduct

Be respectful, inclusive, and professional at all times.

---

## Getting Started

1. Fork the repository (external contributors) or clone directly (team members)
2. Create a branch using the naming convention described in the README
3. Make your changes with appropriate tests
4. Open a Pull Request

---

## Branch Naming

Create one branch **per Jira Story / feature** (not per developer):

```
feature/<rollno>-<jiraid>-story-title
```

**Examples:**
```
feature/21f1001234-TPS-12-authentication
feature/21f1001234-TPS-15-report-pothole
feature/21f1001234-TPS-20-citizen-dashboard
```

---

## Commit Messages

Follow the Conventional Commits specification:

```
<type>(<scope>): <subject>
```

| Type | When to use |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation changes only |
| `style` | Code style changes (formatting, etc.) |
| `refactor` | Code refactor without feature/bug change |
| `test` | Adding or updating tests |
| `chore` | Build process, tooling changes |

---

## Pull Request Guidelines

- Fill in the PR template completely
- Link the related Jira ticket
- Ensure all CI checks pass
- Request review from **Scrum Master or Project Manager**
- Minimum **1 approval** required before merge
- Do not merge your own PR
- Feature branches merge into `dev`
- After sprint completion, `dev` is merged into `main`

---

## Coding Standards

### Python (Backend)
- Follow **PEP 8**
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Minimum test coverage: **80%**

### JavaScript/Vue (Frontend)
- Follow **Vue Style Guide** (Priority A & B rules)
- Use Composition API with `<script setup>`
- Use Pinia for all shared state
- Component names must be PascalCase

---

## Running Tests

### Backend
```bash
cd backend
pytest --cov=app tests/
```

### Frontend
```bash
cd frontend
npm run test
```

---

## Reporting Issues

Use the GitHub Issue templates provided in `.github/ISSUE_TEMPLATE/`.
