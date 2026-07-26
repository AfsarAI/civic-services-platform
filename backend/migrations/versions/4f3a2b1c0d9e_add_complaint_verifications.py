"""add complaint verifications

Revision ID: 4f3a2b1c0d9e
Revises: 210a62c37dc1
Create Date: 2026-07-25

"""

from alembic import op
import sqlalchemy as sa


revision = "4f3a2b1c0d9e"
down_revision = "210a62c37dc1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "complaint_verifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("complaint_id", sa.Integer(), nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("administrator_id", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("repair_completed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["administrator_id"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["complaint_assignments.id"],
        ),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "assignment_id",
            "repair_completed_at",
            name="uq_verification_assignment_completion",
        ),
    )
    op.create_index(
        op.f("ix_complaint_verifications_administrator_id"),
        "complaint_verifications",
        ["administrator_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_complaint_verifications_assignment_id"),
        "complaint_verifications",
        ["assignment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_complaint_verifications_complaint_id"),
        "complaint_verifications",
        ["complaint_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_complaint_verifications_created_at"),
        "complaint_verifications",
        ["created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_complaint_verifications_created_at"),
        table_name="complaint_verifications",
    )
    op.drop_index(
        op.f("ix_complaint_verifications_complaint_id"),
        table_name="complaint_verifications",
    )
    op.drop_index(
        op.f("ix_complaint_verifications_assignment_id"),
        table_name="complaint_verifications",
    )
    op.drop_index(
        op.f("ix_complaint_verifications_administrator_id"),
        table_name="complaint_verifications",
    )
    op.drop_table("complaint_verifications")
