"""Add corner_segment table

Revision ID: 007
Revises: 006
Create Date: 2024-12-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create corner_segment table."""
    op.create_table(
        "corner_segment",
        sa.Column("track_boundary_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_distance", sa.Float(), nullable=False),
        sa.Column("end_distance", sa.Float(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["track_boundary_id"],
            ["track_boundary.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("track_boundary_id", "sort_order", name="uq_corner_segment_order"),
    )
    op.create_index(
        "idx_corner_segment_boundary",
        "corner_segment",
        ["track_boundary_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop corner_segment table."""
    op.drop_index("idx_corner_segment_boundary", table_name="corner_segment")
    op.drop_table("corner_segment")
