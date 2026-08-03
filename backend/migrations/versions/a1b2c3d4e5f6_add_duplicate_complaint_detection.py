"""add duplicate complaint detection fields

Revision ID: a1b2c3d4e5f6
Revises: 7e2b9c4a1d3f
Create Date: 2026-08-03 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "7e2b9c4a1d3f"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("complaints", schema=None) as batch_op:
        batch_op.add_column(sa.Column("duplicate_of_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("duplicate_reason", sa.Text(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_complaints_duplicate_of_id"), ["duplicate_of_id"], unique=False
        )
        batch_op.create_foreign_key(
            "fk_complaints_duplicate_of_id_complaints",
            "complaints",
            ["duplicate_of_id"],
            ["id"],
        )

    with op.batch_alter_table("system_settings", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "duplicate_detection_radius_meters",
                sa.Integer(),
                nullable=False,
                server_default="50",
            )
        )


def downgrade():
    with op.batch_alter_table("system_settings", schema=None) as batch_op:
        batch_op.drop_column("duplicate_detection_radius_meters")

    with op.batch_alter_table("complaints", schema=None) as batch_op:
        batch_op.drop_constraint("fk_complaints_duplicate_of_id_complaints", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_complaints_duplicate_of_id"))
        batch_op.drop_column("duplicate_reason")
        batch_op.drop_column("duplicate_of_id")
