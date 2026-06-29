"""
Pytest configuration and shared fixtures.
"""

import pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    """Create a Flask application instance for testing."""
    application = create_app("testing")

    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    """Provide database access with automatic rollback after each test."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()

        yield _db

        transaction.rollback()
        connection.close()
