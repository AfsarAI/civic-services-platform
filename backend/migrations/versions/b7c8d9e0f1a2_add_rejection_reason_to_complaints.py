"""add rejection reason to complaints

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-08-18 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "b7c8d9e0f1a2"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("complaints", schema=None) as batch_op:
        batch_op.add_column(sa.Column("rejection_reason", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("complaints", schema=None) as batch_op:
        batch_op.drop_column("rejection_reason")