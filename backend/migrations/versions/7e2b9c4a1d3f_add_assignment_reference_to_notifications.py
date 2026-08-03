"""add assignment reference to notifications

Revision ID: 7e2b9c4a1d3f
Revises: f5a6b7c8d9e0
Create Date: 2026-08-01 14:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7e2b9c4a1d3f"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.add_column(sa.Column("related_assignment_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_notifications_related_assignment_id_complaint_assignments",
            "complaint_assignments",
            ["related_assignment_id"],
            ["id"],
        )
        batch_op.create_index(
            "uq_notifications_user_type_assignment",
            ["user_id", "notification_type", "related_assignment_id"],
            unique=True,
        )


def downgrade():
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.drop_index("uq_notifications_user_type_assignment")
        batch_op.drop_constraint(
            "fk_notifications_related_assignment_id_complaint_assignments",
            type_="foreignkey",
        )
        batch_op.drop_column("related_assignment_id")
