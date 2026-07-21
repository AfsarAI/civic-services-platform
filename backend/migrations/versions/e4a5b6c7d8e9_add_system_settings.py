"""add system_settings table

Revision ID: e4a5b6c7d8e9
Revises: d3f4a5b6c7d8
Create Date: 2026-07-20 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e4a5b6c7d8e9"
down_revision = "d3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_name", sa.String(length=120), nullable=False),
        sa.Column("support_email", sa.String(length=120), nullable=True),
        sa.Column("maintenance_mode", sa.Boolean(), nullable=False),
        sa.Column("notify_on_status_change", sa.Boolean(), nullable=False),
        sa.Column("default_complaint_priority", sa.String(length=20), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("system_settings")
