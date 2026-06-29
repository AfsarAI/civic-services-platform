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

## Test File Naming

| Type | Pattern |
|---|---|
| Unit test | `test_<module>.py` |
| Integration test | `test_<endpoint>_api.py` |

## TODO

- [ ] Add test plan document
- [ ] Add test case matrix
- [ ] Document Postman test runs
