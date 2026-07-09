"""add avatar_url to users

Revision ID: d3f4a5b6c7d8
Revises: c8a1f2e3d4b5
Create Date: 2026-07-09 15:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d3f4a5b6c7d8"
down_revision = "c8a1f2e3d4b5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("avatar_url", sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("avatar_url")
