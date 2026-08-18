"""
Civic Services Platform — Application Configuration
"""

import os
from datetime import timedelta
from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _build_cors_origins() -> list[str]:
    """Build allowed CORS origins with safe local development defaults."""
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    configured = [origin.strip() for origin in raw.split(",") if origin.strip()]

    # Only fall back to the local Vite dev origins outside production, so a
    # misconfigured CORS_ORIGINS in prod doesn't silently also trust localhost.
    if os.getenv("FLASK_ENV", "development") != "production":
        defaults = ["http://localhost:5173", "http://127.0.0.1:5173"]
        configured = list(dict.fromkeys(configured + defaults))
    return configured


def _normalize_database_url(url: str) -> str:
    """Normalize legacy postgres:// scheme (some providers still emit it) to
    the postgresql:// scheme SQLAlchemy/psycopg2 expect."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    """Base configuration."""

    # Application
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    DEBUG = False
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(
        os.getenv(
            "DATABASE_URL",
            f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'civic.db')}",
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-change-me-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = "HS256"

    # CORS
    CORS_ORIGINS = _build_cors_origins()

    # Flask-RESTX / Swagger
    RESTX_SWAGGER_UI_DOC_EXPANSION = "list"
    RESTX_VALIDATE = True
    RESTX_MASK_SWAGGER = False
    ERROR_404_HELP = False

    # Pagination defaults
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # StaticPool ensures all connections (fixtures + HTTP requests) share
    # the same in-memory SQLite DB so seeded data is visible to test requests.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    SQLALCHEMY_ECHO = False


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
