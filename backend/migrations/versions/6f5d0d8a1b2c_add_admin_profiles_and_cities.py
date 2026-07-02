"""add cities and administrator profiles

Revision ID: 6f5d0d8a1b2c
Revises: aad82814da50
Create Date: 2026-07-02 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6f5d0d8a1b2c"
down_revision = "aad82814da50"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    with op.batch_alter_table("cities", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_cities_name"), ["name"], unique=True)

    op.create_table(
        "administrator_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("admin_level", sa.String(length=20), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "("
            "admin_level = 'system' AND city_id IS NULL"
            ") OR ("
            "admin_level = 'municipal' AND city_id IS NOT NULL"
            ")",
            name="ck_admin_profiles_level_city_scope",
        ),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    with op.batch_alter_table("administrator_profiles", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_administrator_profiles_admin_level"),
            ["admin_level"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_administrator_profiles_city_id"),
            ["city_id"],
            unique=False,
        )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            INSERT INTO administrator_profiles (user_id, admin_level, city_id, created_by_id, created_at, updated_at)
            SELECT users.id, 'system', NULL, NULL, users.created_at, users.updated_at
            FROM users
            JOIN roles ON roles.id = users.role_id
            WHERE roles.name = 'administrator'
            """
        )
    )


def downgrade():
    with op.batch_alter_table("administrator_profiles", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_administrator_profiles_city_id"))
        batch_op.drop_index(batch_op.f("ix_administrator_profiles_admin_level"))

    op.drop_table("administrator_profiles")

    with op.batch_alter_table("cities", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_cities_name"))

    op.drop_table("cities")
