"""
Standardised API response helpers.
"""

from typing import Any


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
) -> tuple[dict, int]:
    """Return a standardised success response."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "errors": None,
    }, status_code


def error_response(
    message: str = "An error occurred",
    errors: Any = None,
    status_code: int = 400,
) -> tuple[dict, int]:
    """Return a standardised error response."""
    return {
        "success": False,
        "message": message,
        "data": None,
        "errors": errors,
    }, status_code


def paginated_response(
    data: list,
    total: int,
    page: int,
    per_page: int,
    message: str = "Success",
) -> tuple[dict, int]:
    """Return a standardised paginated response."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        },
        "errors": None,
    }, 200
