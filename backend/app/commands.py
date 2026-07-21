"""
Flask CLI commands for database management.

Usage:
    flask seed          # create roles + default admin user (idempotent)
    flask import-pincodes  # import city-pincode mappings from CSV
"""

import csv
import os
import click
from flask import current_app
from flask.cli import with_appcontext

from app.extensions import db
from app.models.administrator_profile import AdministratorProfile
from app.models.city import City
from app.models.city_pincode import CityPincode
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


@click.command("import-pincodes")
@click.option(
    "--csv-path",
    default=None,
    help="Absolute or relative path to pincode CSV. Defaults to ../database/pincode.csv",
)
@click.option(
    "--limit",
    default=None,
    type=int,
    help="Optional row limit for quick local testing.",
)
@click.option(
    "--replace",
    is_flag=True,
    help="Delete existing city/pincode mappings before import.",
)
@with_appcontext
def import_pincodes_command(csv_path: str | None, limit: int | None, replace: bool):
    """Import city+pincode master data into DB from CSV."""
    resolved_csv_path = _resolve_pincode_csv_path(csv_path)
    if not os.path.exists(resolved_csv_path):
        click.echo(f"ERROR: CSV file not found at {resolved_csv_path}", err=True)
        return

    if replace:
        click.echo("Clearing existing pincode mappings...")
        CityPincode.query.delete()
        db.session.commit()

    imported_rows, imported_cities, imported_mappings = _import_pincode_rows(
        csv_path=resolved_csv_path,
        limit=limit,
    )
    db.session.commit()

    click.echo(
        "Import complete. "
        f"rows={imported_rows}, created_or_updated_cities={imported_cities}, "
        f"created_or_updated_mappings={imported_mappings}"
    )


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


def _resolve_pincode_csv_path(csv_path: str | None) -> str:
    if csv_path:
        return os.path.abspath(csv_path)
    return os.path.abspath(
        os.path.join(current_app.root_path, "..", "..", "database", "pincode.csv")
    )


def _import_pincode_rows(csv_path: str, limit: int | None = None) -> tuple[int, int, int]:
    rows_seen = 0
    cities_touched = 0
    mappings_touched = 0
    city_cache: dict[str, City] = {}

    with open(csv_path, mode="r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows_seen += 1
            if limit is not None and rows_seen > limit:
                break

            pincode = (row.get("Pincode") or "").strip()
            if not pincode or not pincode.isdigit() or len(pincode) != 6:
                continue

            city_name = _extract_city_name(row.get("District"), row.get("OfficeName"))
            state_name = (row.get("StateName") or "").strip().title() or None
            district = (row.get("District") or "").strip().title() or None
            area_name = (row.get("OfficeName") or "").strip() or None

            city_key = city_name.lower()
            city = city_cache.get(city_key)
            if not city:
                city = City.query.filter(db.func.lower(City.name) == city_key).first()
                if city:
                    city_cache[city_key] = city

            if not city:
                city = City(name=city_name, state=state_name, is_active=True)
                db.session.add(city)
                db.session.flush()
                city_cache[city_key] = city
                cities_touched += 1
            elif state_name and not city.state:
                city.state = state_name

            mapping = CityPincode.query.filter_by(
                pincode=pincode,
                city_id=city.id,
                area_name=area_name,
            ).first()
            if not mapping:
                mapping = CityPincode(
                    pincode=pincode,
                    city_id=city.id,
                    area_name=area_name,
                    district=district,
                    state=state_name,
                    is_active=True,
                )
                db.session.add(mapping)
                mappings_touched += 1
            else:
                mapping.is_active = True
                if district and not mapping.district:
                    mapping.district = district
                if state_name and not mapping.state:
                    mapping.state = state_name

    return rows_seen if limit is None else min(rows_seen, limit), cities_touched, mappings_touched


def _extract_city_name(district: str | None, office_name: str | None) -> str:
    raw = (district or "").strip()
    if raw:
        return raw.title()

    raw = (office_name or "").strip()
    if not raw:
        return "Unknown"

    # Office names are typically of the form "Area B.O"; use the first segment.
    if " " in raw:
        return raw.split(" ")[0].title()
    return raw.title()
