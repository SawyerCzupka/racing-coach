"""Initial schema with TimescaleDB hypertable

Revision ID: 001
Revises:
Create Date: 2025-11-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create TimescaleDB extension
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")

    # Create track_session table
    op.create_table(
        "track_session",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("track_name", sa.String(length=255), nullable=False),
        sa.Column("track_config_name", sa.String(length=255), nullable=True),
        sa.Column("track_type", sa.String(length=50), nullable=False),
        sa.Column("car_id", sa.Integer(), nullable=False),
        sa.Column("car_name", sa.String(length=255), nullable=False),
        sa.Column("car_class_id", sa.Integer(), nullable=False),
        sa.Column("series_id", sa.Integer(), nullable=False),
        sa.Column("session_type", sa.String(length=255), nullable=False),
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
    )
    op.create_index("idx_session_track_id", "track_session", ["track_id"], unique=False)
    op.create_index("idx_session_car_id", "track_session", ["car_id"], unique=False)
    op.create_index(
        "idx_session_track_id_car_id",
        "track_session",
        ["track_id", "car_id"],
        unique=False,
    )

    # Create lap table
    op.create_table(
        "lap",
        sa.Column("track_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lap_number", sa.Integer(), nullable=False),
        sa.Column("lap_time", sa.Float(), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False),
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
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["track_session_id"],
            ["track_session.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "track_session_id", "lap_number", name="uq_track_session_id_lap_number"
        ),
    )
    op.create_index(
        "idx_track_session_id_lap_number",
        "lap",
        ["track_session_id", "lap_number"],
        unique=False,
    )

    # Create telemetry table
    op.create_table(
        "telemetry",
        sa.Column("track_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lap_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("session_time", sa.Float(), nullable=False),
        sa.Column("lap_number", sa.Integer(), nullable=False),
        sa.Column("lap_distance_pct", sa.Float(), nullable=False),
        sa.Column("lap_distance", sa.Float(), nullable=False),
        sa.Column("current_lap_time", sa.Float(), nullable=False),
        sa.Column("last_lap_time", sa.Float(), nullable=True),
        sa.Column("best_lap_time", sa.Float(), nullable=True),
        sa.Column("speed", sa.Float(), nullable=False),
        sa.Column("rpm", sa.Float(), nullable=False),
        sa.Column("gear", sa.Integer(), nullable=False),
        sa.Column("throttle", sa.Float(), nullable=False),
        sa.Column("brake", sa.Float(), nullable=False),
        sa.Column("clutch", sa.Float(), nullable=False),
        sa.Column("steering_angle", sa.Float(), nullable=False),
        sa.Column("lateral_acceleration", sa.Float(), nullable=False),
        sa.Column("longitudinal_acceleration", sa.Float(), nullable=False),
        sa.Column("vertical_acceleration", sa.Float(), nullable=False),
        sa.Column("yaw_rate", sa.Float(), nullable=False),
        sa.Column("roll_rate", sa.Float(), nullable=False),
        sa.Column("pitch_rate", sa.Float(), nullable=False),
        sa.Column("velocity_x", sa.Float(), nullable=False),
        sa.Column("velocity_y", sa.Float(), nullable=False),
        sa.Column("velocity_z", sa.Float(), nullable=False),
        sa.Column("yaw", sa.Float(), nullable=False),
        sa.Column("pitch", sa.Float(), nullable=False),
        sa.Column("roll", sa.Float(), nullable=False),
        sa.Column("altitude", sa.Float(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        # Tire temperatures
        sa.Column("lf_tire_temp_left", sa.Float(), nullable=True),
        sa.Column("lf_tire_temp_middle", sa.Float(), nullable=True),
        sa.Column("lf_tire_temp_right", sa.Float(), nullable=True),
        sa.Column("rf_tire_temp_left", sa.Float(), nullable=True),
        sa.Column("rf_tire_temp_middle", sa.Float(), nullable=True),
        sa.Column("rf_tire_temp_right", sa.Float(), nullable=True),
        sa.Column("lr_tire_temp_left", sa.Float(), nullable=True),
        sa.Column("lr_tire_temp_middle", sa.Float(), nullable=True),
        sa.Column("lr_tire_temp_right", sa.Float(), nullable=True),
        sa.Column("rr_tire_temp_left", sa.Float(), nullable=True),
        sa.Column("rr_tire_temp_middle", sa.Float(), nullable=True),
        sa.Column("rr_tire_temp_right", sa.Float(), nullable=True),
        # Tire wear
        sa.Column("lf_tire_wear_left", sa.Float(), nullable=True),
        sa.Column("lf_tire_wear_middle", sa.Float(), nullable=True),
        sa.Column("lf_tire_wear_right", sa.Float(), nullable=True),
        sa.Column("rf_tire_wear_left", sa.Float(), nullable=True),
        sa.Column("rf_tire_wear_middle", sa.Float(), nullable=True),
        sa.Column("rf_tire_wear_right", sa.Float(), nullable=True),
        sa.Column("lr_tire_wear_left", sa.Float(), nullable=True),
        sa.Column("lr_tire_wear_middle", sa.Float(), nullable=True),
        sa.Column("lr_tire_wear_right", sa.Float(), nullable=True),
        sa.Column("rr_tire_wear_left", sa.Float(), nullable=True),
        sa.Column("rr_tire_wear_middle", sa.Float(), nullable=True),
        sa.Column("rr_tire_wear_right", sa.Float(), nullable=True),
        # Brake pressure
        sa.Column("lf_brake_pressure", sa.Float(), nullable=True),
        sa.Column("rf_brake_pressure", sa.Float(), nullable=True),
        sa.Column("lr_brake_pressure", sa.Float(), nullable=True),
        sa.Column("rr_brake_pressure", sa.Float(), nullable=True),
        # Track conditions
        sa.Column("track_temp", sa.Float(), nullable=True),
        sa.Column("track_wetness", sa.Integer(), nullable=True),
        sa.Column("air_temp", sa.Float(), nullable=True),
        # Session state
        sa.Column("session_flags", sa.Integer(), nullable=True),
        sa.Column("track_surface", sa.Integer(), nullable=True),
        sa.Column("on_pit_road", sa.Boolean(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["track_session_id"],
            ["track_session.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["lap_id"],
            ["lap.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("timestamp"),
    )

    # Create indexes on telemetry table
    op.create_index("idx_telemetry_lap_id", "telemetry", ["lap_id"], unique=False)
    op.create_index(
        "idx_telemetry_track_session_id",
        "telemetry",
        ["track_session_id"],
        unique=False,
    )
    op.create_index("idx_telemetry_timestamp", "telemetry", ["timestamp"], unique=False)
    op.create_index("idx_session_time", "telemetry", ["session_time"], unique=False)

    # Convert telemetry table to TimescaleDB hypertable
    # Note: This must be done AFTER creating the table and BEFORE inserting any data
    op.execute(
        """
        SELECT create_hypertable(
            'telemetry',
            'timestamp',
            chunk_time_interval => INTERVAL '7 days',
            if_not_exists => TRUE
        )
        """
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table("telemetry")
    op.drop_table("lap")
    op.drop_table("track_session")

    # Drop TimescaleDB extension
    op.execute("DROP EXTENSION IF EXISTS timescaledb CASCADE")
