"""Create the complaints table.

Revision ID: 0001
Revises:
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    category = sa.Enum("water", "electricity", "sanitation", "roads", "streetlights", "other", name="category_enum")
    priority = sa.Enum("high", "normal", "low", name="priority_enum")
    status = sa.Enum("open", "in_progress", "resolved", "rejected", name="status_enum")
    op.create_table(
        "complaints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column("reporter_contact", sa.String(length=200), nullable=True),
        sa.Column("category", category, nullable=False),
        sa.Column("priority", priority, nullable=False),
        sa.Column("status", status, server_default="open", nullable=False),
        sa.Column("ai_summary", sa.String(length=140), nullable=True),
        sa.Column("triaged_by", sa.String(length=30), nullable=False),
        sa.Column("triage_latency_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("char_length(text) BETWEEN 10 AND 2000", name="ck_complaints_text_length"),
        sa.CheckConstraint("char_length(location) BETWEEN 3 AND 200", name="ck_complaints_location_length"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_complaints_status_priority", "complaints", ["status", "priority"])
    op.create_index("ix_complaints_created_at", "complaints", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_complaints_created_at", table_name="complaints")
    op.drop_index("ix_complaints_status_priority", table_name="complaints")
    op.drop_table("complaints")
    sa.Enum(name="status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="priority_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="category_enum").drop(op.get_bind(), checkfirst=True)

