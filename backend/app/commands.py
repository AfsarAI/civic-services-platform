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
from app.models.administrator_profile import AdministratorProfile
from app.models.role import Role
from app.models.user import User


# ── Role definitions ──────────────────────────────────────────────────────
# Exactly 3 roles per Milestone1_Report.pdf Section 2.4.
# Administrator is a consolidated role covering complaint management,
# reporting, user management, and system administration.

ROLES = [
    {"name": Role.CITIZEN, "description": "Registered citizen who can report and track complaints"},
    {"name": Role.FIELD_WORKER, "description": "Field worker / engineer who carries out repairs"},
    {"name": Role.ADMINISTRATOR, "description": (
        "Consolidated administrator: complaint management, assignment, "
        "monitoring, reports, user management, and system administration"
    )},
]


@click.command("seed")
@with_appcontext
def seed_command():
    """Seed the database with roles and a default system admin user (idempotent)."""

    click.echo("Seeding roles...")
    _seed_roles()

    click.echo("Seeding system administrator...")
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
    """Create the default system administrator from environment variables."""
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
        if existing.admin_profile:
            click.echo(f"  System administrator '{email}' already exists — skipped.")
            return

        db.session.add(
            AdministratorProfile(
                user_id=existing.id,
                admin_level=AdministratorProfile.SYSTEM,
                city_id=None,
                created_by_id=None,
            )
        )
        db.session.commit()
        click.echo(f"  Added missing system administrator profile for: {email}")
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
    db.session.flush()

    db.session.add(
        AdministratorProfile(
            user_id=admin.id,
            admin_level=AdministratorProfile.SYSTEM,
            city_id=None,
            created_by_id=None,
        )
    )
    db.session.commit()

    click.echo(f"  Created system administrator: {email}")
    if current_app.debug:
        click.echo(f"  Password: {password}  (shown only in DEBUG mode)")
