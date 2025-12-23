"""Add is_admin column to user table

Revision ID: 005
Revises: 004
Create Date: 2024-12-22

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add is_admin column to user table."""
    op.add_column(
        "user",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("idx_user_is_admin", "user", ["is_admin"], unique=False)


def downgrade() -> None:
    """Remove is_admin column from user table."""
    op.drop_index("idx_user_is_admin", table_name="user")
    op.drop_column("user", "is_admin")
