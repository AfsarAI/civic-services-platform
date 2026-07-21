"""add evidence_url to complaint_assignments

Revision ID: c8a1f2e3d4b5
Revises: b3d7d4f4c1aa
Create Date: 2026-07-09 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c8a1f2e3d4b5"
down_revision = "b3d7d4f4c1aa"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("complaint_assignments", schema=None) as batch_op:
        batch_op.add_column(sa.Column("evidence_url", sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table("complaint_assignments", schema=None) as batch_op:
        batch_op.drop_column("evidence_url")
