"""
Civic Services Platform — Application Factory
"""

from flask import Flask
from flask_cors import CORS

from config import config_map
from app.extensions import db, migrate, jwt, ma


def create_app(config_name: str = "development") -> Flask:
    """Create and configure the Flask application."""

    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    app.config.from_object(config_map.get(config_name, config_map["default"]))

    # Initialise extensions
    _init_extensions(app)

    # Register API blueprints
    _register_blueprints(app)

    # Register CLI commands
    _register_commands(app)

    # Register error handlers
    _register_error_handlers(app)

    return app


def _init_extensions(app: Flask) -> None:
    """Initialise all Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)

    CORS(app, origins=app.config.get("CORS_ORIGINS", ["*"]))

    # Import models here so SQLAlchemy (and Alembic) can discover them
    import app.models  # noqa: F401


def _register_blueprints(app: Flask) -> None:
    """Register all API blueprints."""
    from app.api import api_bp

    app.register_blueprint(api_bp, url_prefix="/api/v1")


def _register_commands(app: Flask) -> None:
    """Register Flask CLI commands."""
    from app.commands import import_pincodes_command, seed_command

    app.cli.add_command(seed_command)
    app.cli.add_command(import_pincodes_command)


def _register_error_handlers(app: Flask) -> None:
    """Register global error handlers."""
    from flask import jsonify

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "message": "Bad request", "errors": str(error)}), 400

    @app.errorhandler(401)
    def unauthorised(error):
        return jsonify({"success": False, "message": "Unauthorised", "errors": str(error)}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"success": False, "message": "Forbidden", "errors": str(error)}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "message": "Resource not found", "errors": str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"success": False, "message": "Internal server error", "errors": str(error)}), 500
