"""
Flask CLI commands for database management.

Usage:
    flask seed          # create roles + default admin user (idempotent)
"""

import os
import click
from flask import current_app
from flask.cli import with_appcontext

from app.extensions import db
from app.models.role import Role
from app.models.user import User


# ── Role definitions ──────────────────────────────────────────────────────

ROLES = [
    {"name": Role.CITIZEN, "description": "Registered citizen who can report and track complaints"},
    {"name": Role.ADMINISTRATOR, "description": "Municipal administrator who manages complaints"},
    {"name": Role.FIELD_WORKER, "description": "Field worker / engineer who carries out repairs"},
    {"name": "senior_management", "description": "Senior officer who monitors performance"},
    {"name": "sysadmin", "description": "System administrator who manages users and platform"},
]


@click.command("seed")
@with_appcontext
def seed_command():
    """Seed the database with roles and a default admin user (idempotent)."""

    click.echo("Seeding roles...")
    _seed_roles()

    click.echo("Seeding admin user...")
    _seed_admin()

    click.echo("Done. Database seeded successfully.")


def _seed_roles():
    """Create all roles if they do not already exist."""
    for role_data in ROLES:
        existing = Role.query.filter_by(name=role_data["name"]).first()
        if existing:
            click.echo(f"  Role '{role_data['name']}' already exists — skipped.")
        else:
            role = Role(name=role_data["name"], description=role_data["description"])
            db.session.add(role)
            click.echo(f"  Created role '{role_data['name']}'.")
    db.session.commit()


def _seed_admin():
    """Create the default admin user from environment variables."""
    email = os.environ.get("ADMIN_EMAIL", "admin@civicservices.local")
    password = os.environ.get("ADMIN_PASSWORD", "Admin@123456")
    first_name = os.environ.get("ADMIN_FIRST_NAME", "System")
    last_name = os.environ.get("ADMIN_LAST_NAME", "Administrator")

    if not password or len(password) < 8:
        click.echo(
            "  ERROR: ADMIN_PASSWORD must be at least 8 characters. "
            "Set it in your .env file.",
            err=True,
        )
        return

    existing = User.query.filter_by(email=email).first()
    if existing:
        click.echo(f"  Admin user '{email}' already exists — skipped.")
        return

    admin_role = Role.query.filter_by(name=Role.ADMINISTRATOR).first()
    if not admin_role:
        click.echo("  ERROR: Administrator role not found. Run `flask seed` again.", err=True)
        return

    admin = User(
        username="admin",
        email=email,
        first_name=first_name,
        last_name=last_name,
        role_id=admin_role.id,
        is_active=True,
    )
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()

    click.echo(f"  Created admin user: {email}")
    if current_app.debug:
        click.echo(f"  Password: {password}  (shown only in DEBUG mode)")
