"""
Shared schema validators and normalizers.
"""

import re

from marshmallow import ValidationError


PHONE_PATTERN = re.compile(r"^\+?(\d[\s\-]?){9,14}\d$")


def normalize_email(value: str | None) -> str | None:
    """Return a trimmed, lower-cased email address."""
    if not isinstance(value, str):
        return value
    return value.strip().lower()


def normalize_string(value: str | None) -> str | None:
    """Return a trimmed string, preserving non-string values as-is."""
    if not isinstance(value, str):
        return value
    return value.strip()


def normalize_optional_string(value: str | None) -> str | None:
    """Return a trimmed string or ``None`` when the input is blank."""
    if not isinstance(value, str):
        return value
    cleaned = value.strip()
    return cleaned or None


def validate_password_strength(value: str) -> None:
    """Enforce password complexity: min 8 chars, uppercase, digit, special."""
    if len(value) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", value):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"\d", value):
        raise ValidationError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_]", value):
        raise ValidationError(
            "Password must contain at least one special character (e.g. @, #, !)."
        )


def validate_phone_number(value: str | None) -> None:
    """Validate a phone number using the shared project format."""
    if value is None:
        return
    if not PHONE_PATTERN.match(value):
        raise ValidationError(
            "Enter a valid phone number (e.g. +91-9876543210 or 9876543210)."
        )
