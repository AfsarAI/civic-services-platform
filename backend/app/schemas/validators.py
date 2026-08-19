"""
Shared schema validators and normalizers.
"""

import re

from marshmallow import ValidationError


PHONE_PATTERN = re.compile(r"^[6-9]\d{9}$")
PINCODE_PATTERN = re.compile(r"^\d{6}$")


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
    """Validate an optional Indian mobile number."""
    if value is None:
        return
    normalized = value.strip() if isinstance(value, str) else value
    if not isinstance(normalized, str) or not PHONE_PATTERN.fullmatch(normalized):
        raise ValidationError("Enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.")


def validate_pincode(value: str | None) -> None:
    """Validate a 6-digit Indian pincode."""
    if value is None:
        return
    if not PINCODE_PATTERN.match(value):
        raise ValidationError("Pincode must be exactly 6 digits.")
