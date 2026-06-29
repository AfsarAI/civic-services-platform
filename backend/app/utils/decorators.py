"""
Authentication decorators for role-based access control.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt

from app.extensions import db


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
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Access denied: insufficient permissions",
                        }
                    ),
                    403,
                )
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
            return jsonify({"success": False, "message": "Citizen access required"}), 403
        return fn(*args, **kwargs)

    return wrapper


def require_admin(fn):
    """Restrict access to administrators only."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") != "administrator":
            return jsonify({"success": False, "message": "Administrator access required"}), 403
        return fn(*args, **kwargs)

    return wrapper


def require_field_worker(fn):
    """Restrict access to field workers only."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") != "field_worker":
            return jsonify({"success": False, "message": "Field worker access required"}), 403
        return fn(*args, **kwargs)

    return wrapper
