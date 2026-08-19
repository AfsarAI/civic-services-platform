"""
Civic Services Platform — Application Factory
"""

import os

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import config_map, BASE_DIR
from app.extensions import db, migrate, jwt, ma

# Populated by the Azure deploy workflow (copy of frontend/dist); absent in
# local dev, where the Vue app is served separately by `npm run dev`.
FRONTEND_DIST_DIR = os.path.join(BASE_DIR, "static_frontend")


def create_app(config_name: str = "development") -> Flask:
    """Create and configure the Flask application."""

    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    app.config.from_object(config_map.get(config_name, config_map["default"]))

    # Initialise extensions
    _init_extensions(app)

    # Register API blueprints
    _register_blueprints(app)

    # Serve the built frontend (if present) from this same app/origin
    _register_frontend(app)

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


def _register_frontend(app: Flask) -> None:
    """Serve the built Vue SPA (frontend/dist) from the same origin as the API.

    No-op unless FRONTEND_DIST_DIR exists, so local `flask run` (API only,
    frontend runs on its own via `npm run dev`) is unaffected.
    """
    if not os.path.isdir(FRONTEND_DIST_DIR):
        return

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        # Safety net only — real /api/v1/* requests are already matched by
        # the blueprint above before Werkzeug ever reaches this catch-all.
        if path.startswith("api/"):
            return jsonify({"success": False, "message": "Not found", "data": None, "errors": None}), 404
        target = os.path.join(FRONTEND_DIST_DIR, path)
        if path and os.path.isfile(target):
            return send_from_directory(FRONTEND_DIST_DIR, path)
        return send_from_directory(FRONTEND_DIST_DIR, "index.html")


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
