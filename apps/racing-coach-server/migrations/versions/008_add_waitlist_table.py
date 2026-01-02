"""Add waitlist_entry table for marketing signups

Revision ID: 008
Revises: 007
Create Date: 2024-12-31

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create waitlist_entry table."""
    op.create_table(
        "waitlist_entry",
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("idx_waitlist_email", "waitlist_entry", ["email"], unique=False)
    op.create_index("idx_waitlist_created_at", "waitlist_entry", ["created_at"], unique=False)


def downgrade() -> None:
    """Drop waitlist_entry table."""
    op.drop_index("idx_waitlist_created_at", table_name="waitlist_entry")
    op.drop_index("idx_waitlist_email", table_name="waitlist_entry")
    op.drop_table("waitlist_entry")
