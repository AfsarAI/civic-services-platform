# Testing Documentation

This folder contains test plans, test cases, and testing reports for the Civic Services Platform.

## Test Strategy

| Layer | Tool | Scope |
|---|---|---|
| Unit Tests | Pytest | Models, services, utilities |
| Integration Tests | Pytest + Flask test client | API endpoints |
| API Tests | Postman | End-to-end API flows |
| Frontend Tests | Vitest (future) | Vue components |

## Running Tests

### Backend

```bash
cd backend

# All tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=app --cov-report=html

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v
```

### Coverage Target

Minimum acceptable coverage: **80%**

## TPS-110 Coverage

Current automated coverage for Municipal Administrator registration includes:
- successful System Administrator registration of a Municipal Administrator
- duplicate email conflict handling
- anonymous and citizen access denial
- password, confirm-password, and phone validation failures
- Municipal Administrator login with `admin_level` and `city_name`
- service-level audit-log creation for municipal-administrator registration

## Test File Naming

| Type | Pattern |
|---|---|
| Unit test | `test_<module>.py` |
| Integration test | `test_<endpoint>_api.py` |

## TODO

- [ ] Add test plan document
- [ ] Add test case matrix
- [ ] Document Postman test runs
