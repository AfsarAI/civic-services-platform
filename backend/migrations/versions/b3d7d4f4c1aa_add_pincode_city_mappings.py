"""add pincode mappings and city linkage fields

Revision ID: b3d7d4f4c1aa
Revises: 6f5d0d8a1b2c
Create Date: 2026-07-07 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b3d7d4f4c1aa"
down_revision = "6f5d0d8a1b2c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "city_pincodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pincode", sa.String(length=6), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("area_name", sa.String(length=120), nullable=True),
        sa.Column("district", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pincode", "city_id", "area_name", name="uq_city_pincode_city_area"),
    )
    with op.batch_alter_table("city_pincodes", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_city_pincodes_pincode"), ["pincode"], unique=False)
        batch_op.create_index(batch_op.f("ix_city_pincodes_city_id"), ["city_id"], unique=False)

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("city_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("pincode", sa.String(length=6), nullable=True))
        batch_op.create_index(batch_op.f("ix_users_city_id"), ["city_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_users_pincode"), ["pincode"], unique=False)
        batch_op.create_foreign_key("fk_users_city_id_cities", "cities", ["city_id"], ["id"])

    with op.batch_alter_table("complaints", schema=None) as batch_op:
        batch_op.add_column(sa.Column("city_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("pincode", sa.String(length=6), nullable=True))
        batch_op.create_index(batch_op.f("ix_complaints_city_id"), ["city_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_complaints_pincode"), ["pincode"], unique=False)
        batch_op.create_foreign_key("fk_complaints_city_id_cities", "cities", ["city_id"], ["id"])


def downgrade():
    with op.batch_alter_table("complaints", schema=None) as batch_op:
        batch_op.drop_constraint("fk_complaints_city_id_cities", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_complaints_pincode"))
        batch_op.drop_index(batch_op.f("ix_complaints_city_id"))
        batch_op.drop_column("pincode")
        batch_op.drop_column("city_id")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("fk_users_city_id_cities", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_users_pincode"))
        batch_op.drop_index(batch_op.f("ix_users_city_id"))
        batch_op.drop_column("pincode")
        batch_op.drop_column("city_id")

    with op.batch_alter_table("city_pincodes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_city_pincodes_city_id"))
        batch_op.drop_index(batch_op.f("ix_city_pincodes_pincode"))

    op.drop_table("city_pincodes")
