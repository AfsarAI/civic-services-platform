"""add closed_at to complaints

Revision ID: f5a6b7c8d9e0
Revises: 4f3a2b1c0d9e
Create Date: 2026-07-31 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "f5a6b7c8d9e0"
down_revision = "4f3a2b1c0d9e"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("complaints", schema=None) as batch_op:
        batch_op.add_column(sa.Column("closed_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("complaints", schema=None) as batch_op:
        batch_op.drop_column("closed_at")
