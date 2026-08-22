from sqlalchemy import extract, func

from app import db


def duration_hours(start_column, end_column):
    """Return a SQL expression that calculates duration in hours.

    Supports SQLite for local/unit tests and PostgreSQL for production.
    """
    dialect = db.session.get_bind().dialect.name

    if dialect == "postgresql":
        return extract(
            "epoch",
            end_column - start_column
        ) / 3600

    return (
        func.julianday(end_column) -
        func.julianday(start_column)
    ) * 24