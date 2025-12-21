"""Add track_boundary table

Revision ID: 004
Revises: 003
Create Date: 2024-12-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add track_boundary table."""
    op.create_table(
        "track_boundary",
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("track_name", sa.String(length=255), nullable=False),
        sa.Column("track_config_name", sa.String(length=255), nullable=True),
        sa.Column(
            "grid_distance_pct", postgresql.ARRAY(sa.Float()), nullable=False
        ),
        sa.Column("left_latitude", postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column("left_longitude", postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column("right_latitude", postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column("right_longitude", postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column("grid_size", sa.Integer(), nullable=False),
        sa.Column("source_left_frames", sa.Integer(), nullable=False),
        sa.Column("source_right_frames", sa.Integer(), nullable=False),
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
        sa.UniqueConstraint(
            "track_id", "track_config_name", name="uq_track_boundary_track_config"
        ),
    )
    op.create_index(
        "idx_track_boundary_track_id", "track_boundary", ["track_id"], unique=False
    )


def downgrade() -> None:
    """Remove track_boundary table."""
    op.drop_index("idx_track_boundary_track_id", table_name="track_boundary")
    op.drop_table("track_boundary")
