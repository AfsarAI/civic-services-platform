"""
API package — registers all Flask-RESTX namespaces onto a single Blueprint.
"""

from flask import Blueprint
from flask_restx import Api

from app.api.auth.controller import ns as auth_ns
from app.api.citizen.controller import ns as citizen_ns
from app.api.administrator.controller import ns as admin_ns
from app.api.fieldworker.controller import ns as fieldworker_ns
from app.api.reports.controller import ns as reports_ns
from app.api.notifications.controller import ns as notifications_ns
from app.api.locations.controller import ns as locations_ns

api_bp = Blueprint("api", __name__)

api = Api(
    api_bp,
    version="1.0",
    title="Civic Services Platform API",
    description="REST API for the Civic Services Platform",
    doc="/docs",
    authorizations={
        "Bearer": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Enter: **Bearer &lt;JWT token&gt;**",
        }
    },
    security="Bearer",
)

api.add_namespace(auth_ns)
api.add_namespace(citizen_ns)
api.add_namespace(admin_ns)
api.add_namespace(fieldworker_ns)
api.add_namespace(reports_ns)
api.add_namespace(notifications_ns)
api.add_namespace(locations_ns)
