"""Add lap metrics tables

Revision ID: 002
Revises: 001
Create Date: 2025-11-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema to add metrics tables."""
    # Create lap_metrics table
    op.create_table(
        "lap_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lap_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lap_time", sa.Float(), nullable=True),
        sa.Column("total_corners", sa.Integer(), nullable=False),
        sa.Column("total_braking_zones", sa.Integer(), nullable=False),
        sa.Column("average_corner_speed", sa.Float(), nullable=False),
        sa.Column("max_speed", sa.Float(), nullable=False),
        sa.Column("min_speed", sa.Float(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["lap_id"],
            ["lap.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lap_id", name="uq_lap_metrics_lap_id"),
    )
    op.create_index("idx_lap_metrics_lap_id", "lap_metrics", ["lap_id"], unique=False)

    # Create braking_metrics table
    op.create_table(
        "braking_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lap_metrics_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("zone_number", sa.Integer(), nullable=False),
        sa.Column("braking_point_distance", sa.Float(), nullable=False),
        sa.Column("braking_point_speed", sa.Float(), nullable=False),
        sa.Column("end_distance", sa.Float(), nullable=False),
        sa.Column("max_brake_pressure", sa.Float(), nullable=False),
        sa.Column("braking_duration", sa.Float(), nullable=False),
        sa.Column("minimum_speed", sa.Float(), nullable=False),
        sa.Column("initial_deceleration", sa.Float(), nullable=False),
        sa.Column("average_deceleration", sa.Float(), nullable=False),
        sa.Column("braking_efficiency", sa.Float(), nullable=False),
        sa.Column("has_trail_braking", sa.Boolean(), nullable=False),
        sa.Column("trail_brake_distance", sa.Float(), nullable=False),
        sa.Column("trail_brake_percentage", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["lap_metrics_id"],
            ["lap_metrics.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_braking_metrics_lap_metrics_id",
        "braking_metrics",
        ["lap_metrics_id"],
        unique=False,
    )
    op.create_index(
        "idx_braking_metrics_zone_number",
        "braking_metrics",
        ["lap_metrics_id", "zone_number"],
        unique=False,
    )

    # Create corner_metrics table
    op.create_table(
        "corner_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lap_metrics_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("corner_number", sa.Integer(), nullable=False),
        sa.Column("turn_in_distance", sa.Float(), nullable=False),
        sa.Column("apex_distance", sa.Float(), nullable=False),
        sa.Column("exit_distance", sa.Float(), nullable=False),
        sa.Column("throttle_application_distance", sa.Float(), nullable=False),
        sa.Column("turn_in_speed", sa.Float(), nullable=False),
        sa.Column("apex_speed", sa.Float(), nullable=False),
        sa.Column("exit_speed", sa.Float(), nullable=False),
        sa.Column("throttle_application_speed", sa.Float(), nullable=False),
        sa.Column("max_lateral_g", sa.Float(), nullable=False),
        sa.Column("time_in_corner", sa.Float(), nullable=False),
        sa.Column("corner_distance", sa.Float(), nullable=False),
        sa.Column("max_steering_angle", sa.Float(), nullable=False),
        sa.Column("speed_loss", sa.Float(), nullable=False),
        sa.Column("speed_gain", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["lap_metrics_id"],
            ["lap_metrics.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_corner_metrics_lap_metrics_id",
        "corner_metrics",
        ["lap_metrics_id"],
        unique=False,
    )
    op.create_index(
        "idx_corner_metrics_corner_number",
        "corner_metrics",
        ["lap_metrics_id", "corner_number"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade database schema to remove metrics tables."""
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table("corner_metrics")
    op.drop_table("braking_metrics")
    op.drop_table("lap_metrics")
