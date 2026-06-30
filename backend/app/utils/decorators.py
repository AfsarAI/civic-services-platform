"""
Decorators for role-based access control and request body validation.
"""

from functools import wraps
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from marshmallow import ValidationError


def require_role(*roles: str):
    """
    Decorator that restricts endpoint access to users with specified roles.

    Usage:
        @require_role("administrator")
        @require_role("citizen", "administrator")
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")

            if user_role not in roles:
                return {
                    "success": False,
                    "message": "Access denied: insufficient permissions",
                    "data": None,
                    "errors": None,
                }, 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_citizen(fn):
    """Restrict access to citizens only."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") != "citizen":
            return {"success": False, "message": "Citizen access required", "data": None, "errors": None}, 403
        return fn(*args, **kwargs)

    return wrapper


def require_admin(fn):
    """Restrict access to administrators only."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") != "administrator":
            return {"success": False, "message": "Administrator access required", "data": None, "errors": None}, 403
        return fn(*args, **kwargs)

    return wrapper


def require_field_worker(fn):
    """Restrict access to field workers only."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") != "field_worker":
            return {"success": False, "message": "Field worker access required", "data": None, "errors": None}, 403
        return fn(*args, **kwargs)

    return wrapper


def validate_body(schema_class):
    """Validate and deserialize the JSON request body using a Marshmallow schema.

    Injects the validated data as the first positional argument after ``self``
    (for class-based Flask-RESTX Resources).

    Returns 422 with field-level ``errors`` if validation fails.
    Returns 400 if the request body is not valid JSON.

    Usage::

        @validate_body(RegisterRequestSchema)
        def post(self, body):
            # body is already validated and deserialized
            ...
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            json_data = request.get_json(silent=True)
            if json_data is None:
                return {
                    "success": False,
                    "message": "Request body must be valid JSON",
                    "data": None,
                    "errors": None,
                }, 400

            schema = schema_class()
            try:
                validated = schema.load(json_data)
            except ValidationError as exc:
                return {
                    "success": False,
                    "message": "Validation failed",
                    "data": None,
                    "errors": exc.messages,
                }, 422

            # Inject validated data as the first argument after self/cls
            return fn(*args, validated, **kwargs)

        return wrapper

    return decorator
