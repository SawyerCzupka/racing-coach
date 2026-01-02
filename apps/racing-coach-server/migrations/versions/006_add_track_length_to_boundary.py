"""Add track_length column to track_boundary table

Revision ID: 006
Revises: 005
Create Date: 2024-12-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add track_length column to track_boundary table."""
    op.add_column(
        "track_boundary",
        sa.Column("track_length", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    """Remove track_length column from track_boundary table."""
    op.drop_column("track_boundary", "track_length")
