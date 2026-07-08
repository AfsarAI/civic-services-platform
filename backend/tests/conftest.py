"""
Pytest configuration and shared fixtures.
"""

import pytest
from app import create_app
from app.extensions import db as _db




def _seed_roles():
    """Insert the 3 application roles so tests can register/login."""
    from app.models.role import Role
    for name in (Role.CITIZEN, Role.FIELD_WORKER, Role.ADMINISTRATOR):
        if not Role.query.filter_by(name=name).first():
            _db.session.add(Role(name=name))
    _db.session.commit()


def _seed_location_mappings():
    """Insert deterministic city/pincode fixtures for onboarding tests."""
    from app.models.city import City
    from app.models.city_pincode import CityPincode

    city = City.query.filter_by(name="Lucknow").first()
    if not city:
        city = City(name="Lucknow", state="Uttar Pradesh", is_active=True)
        _db.session.add(city)
        _db.session.flush()

    mapping = CityPincode.query.filter_by(pincode="226001", city_id=city.id).first()
    if not mapping:
        _db.session.add(
            CityPincode(
                pincode="226001",
                city_id=city.id,
                area_name="Hazratganj",
                district="Lucknow",
                state="Uttar Pradesh",
                is_active=True,
            )
        )
    _db.session.commit()
@pytest.fixture(scope="session")
def app():
    """Create a Flask application instance for testing."""
    application = create_app("testing")

    with application.app_context():
        _db.create_all()
        _seed_roles()
        _seed_location_mappings()
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
