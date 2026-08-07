"""
Custom SQLAlchemy column type ensuring all stored datetimes round-trip as
timezone-aware UTC values.

Every model in this app stores timestamps using ``datetime.now(timezone.utc)``,
but SQLite (and the plain ``db.DateTime`` type) silently strips the tzinfo on
both write and read, so values loaded back from the database are *naive* even
though they represent UTC instants. When a service then calls
``some_datetime.isoformat()`` to build an API response, the resulting string
has no timezone suffix (e.g. ``"2026-08-01T11:30:00"`` instead of
``"2026-08-01T11:30:00+00:00"``). Browsers/JS then parse that string as
*local* time instead of UTC, silently shifting every displayed date/time by
the viewer's UTC offset (e.g. -5:30 for IST).

``UTCDateTime`` fixes this at the column level: SQLite storage is unchanged
(still the same DATETIME column, no migration needed), but values are
guaranteed to come back out of the ORM already tagged ``tzinfo=timezone.utc``,
so every existing ``.isoformat()`` call in the codebase now produces a
correct, unambiguous timestamp automatically.
"""

from datetime import timezone

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    """A DateTime column that is always UTC and always timezone-aware in Python."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return value.replace(tzinfo=timezone.utc)
