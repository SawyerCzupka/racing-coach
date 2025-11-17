"""SQLAlchemy models for the telemetry feature."""

import uuid
from datetime import datetime

from racing_coach_core.models.telemetry import SessionFrame
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from racing_coach_server.database.base import Base


class TrackSession(Base):
    """Model representing a track session."""

    __tablename__ = "track_session"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    track_id: Mapped[int] = mapped_column(Integer, nullable=False)
    track_name: Mapped[str] = mapped_column(String(255), nullable=False)
    track_config_name: Mapped[str] = mapped_column(String(255), nullable=True)
    track_type: Mapped[str] = mapped_column(String(50), nullable=False)
    car_id: Mapped[int] = mapped_column(Integer, nullable=False)
    car_name: Mapped[str] = mapped_column(String(255), nullable=False)
    car_class_id: Mapped[int] = mapped_column(Integer, nullable=False)
    series_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )

    # Relationships
    laps: Mapped[list["Lap"]] = relationship(
        "Lap", back_populates="track_session", cascade="all, delete-orphan", init=False
    )
    telemetry_frames: Mapped[list["Telemetry"]] = relationship(
        "Telemetry",
        back_populates="track_session",
        cascade="all, delete-orphan",
        init=False,
    )

    # Indexes
    __table_args__ = (
        Index("idx_session_track_id", "track_id"),
        Index("idx_session_car_id", "car_id"),
        Index("idx_session_track_id_car_id", "track_id", "car_id"),
    )

    def to_session_frame(self) -> SessionFrame:
        """Convert TrackSession to SessionFrame."""
        return SessionFrame(
            timestamp=self.created_at,
            session_id=self.id,
            track_id=self.track_id,
            track_name=self.track_name,
            track_config_name=self.track_config_name,
            track_type=self.track_type,
            car_id=self.car_id,
            car_name=self.car_name,
            car_class_id=self.car_class_id,
            series_id=self.series_id,
        )


class Lap(Base):
    """Model representing a lap in a session."""

    __tablename__ = "lap"

    track_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("track_session.id", ondelete="CASCADE"),
        nullable=False,
    )
    lap_number: Mapped[int] = mapped_column(Integer, nullable=False)
    lap_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )

    # Relationships
    track_session: Mapped["TrackSession"] = relationship(
        "TrackSession", back_populates="laps", init=False
    )
    telemetry_frames: Mapped[list["Telemetry"]] = relationship(
        "Telemetry", back_populates="lap", cascade="all, delete-orphan", init=False
    )
    metrics: Mapped["LapMetricsDB | None"] = relationship(
        "LapMetricsDB",
        back_populates="lap",
        cascade="all, delete-orphan",
        init=False,
        uselist=False,
    )
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default_factory=uuid.uuid4
    )

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint("track_session_id", "lap_number", name="uq_track_session_id_lap_number"),
        Index("idx_track_session_id_lap_number", "track_session_id", "lap_number"),
    )


class Telemetry(Base):
    """Model representing a telemetry frame."""

    __tablename__ = "telemetry"

    track_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("track_session.id", ondelete="CASCADE"),
        nullable=False,
    )
    lap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lap.id", ondelete="CASCADE"), nullable=False
    )

    # Time fields
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        server_default=func.now(),
        nullable=False,
    )
    session_time: Mapped[float] = mapped_column(Float, nullable=False)

    # Lap information
    lap_number: Mapped[int] = mapped_column(Integer, nullable=False)
    lap_distance_pct: Mapped[float] = mapped_column(Float, nullable=False)
    lap_distance: Mapped[float] = mapped_column(Float, nullable=False)
    current_lap_time: Mapped[float] = mapped_column(Float, nullable=False)
    last_lap_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_lap_time: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Vehicle state
    speed: Mapped[float] = mapped_column(Float, nullable=False)
    rpm: Mapped[float] = mapped_column(Float, nullable=False)
    gear: Mapped[int] = mapped_column(Integer, nullable=False)

    # Driver inputs
    throttle: Mapped[float] = mapped_column(Float, nullable=False)
    brake: Mapped[float] = mapped_column(Float, nullable=False)
    clutch: Mapped[float] = mapped_column(Float, nullable=False)
    steering_angle: Mapped[float] = mapped_column(Float, nullable=False)

    # Vehicle dynamics
    lateral_acceleration: Mapped[float] = mapped_column(Float, nullable=False)
    longitudinal_acceleration: Mapped[float] = mapped_column(Float, nullable=False)
    vertical_acceleration: Mapped[float] = mapped_column(Float, nullable=False)
    yaw_rate: Mapped[float] = mapped_column(Float, nullable=False)
    roll_rate: Mapped[float] = mapped_column(Float, nullable=False)
    pitch_rate: Mapped[float] = mapped_column(Float, nullable=False)

    # Vehicle position/orientation
    position_x: Mapped[float] = mapped_column(Float, nullable=False)
    position_y: Mapped[float] = mapped_column(Float, nullable=False)
    position_z: Mapped[float] = mapped_column(Float, nullable=False)
    yaw: Mapped[float] = mapped_column(Float, nullable=False)
    pitch: Mapped[float] = mapped_column(Float, nullable=False)
    roll: Mapped[float] = mapped_column(Float, nullable=False)

    # Tire data - flattened for better query performance
    # Left Front
    lf_tire_temp_left: Mapped[float | None] = mapped_column(Float, nullable=True)
    lf_tire_temp_middle: Mapped[float | None] = mapped_column(Float, nullable=True)
    lf_tire_temp_right: Mapped[float | None] = mapped_column(Float, nullable=True)
    lf_tire_wear_left: Mapped[float | None] = mapped_column(Float, nullable=True)
    lf_tire_wear_middle: Mapped[float | None] = mapped_column(Float, nullable=True)
    lf_tire_wear_right: Mapped[float | None] = mapped_column(Float, nullable=True)
    lf_brake_pressure: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Right Front
    rf_tire_temp_left: Mapped[float | None] = mapped_column(Float, nullable=True)
    rf_tire_temp_middle: Mapped[float | None] = mapped_column(Float, nullable=True)
    rf_tire_temp_right: Mapped[float | None] = mapped_column(Float, nullable=True)
    rf_tire_wear_left: Mapped[float | None] = mapped_column(Float, nullable=True)
    rf_tire_wear_middle: Mapped[float | None] = mapped_column(Float, nullable=True)
    rf_tire_wear_right: Mapped[float | None] = mapped_column(Float, nullable=True)
    rf_brake_pressure: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Left Rear
    lr_tire_temp_left: Mapped[float | None] = mapped_column(Float, nullable=True)
    lr_tire_temp_middle: Mapped[float | None] = mapped_column(Float, nullable=True)
    lr_tire_temp_right: Mapped[float | None] = mapped_column(Float, nullable=True)
    lr_tire_wear_left: Mapped[float | None] = mapped_column(Float, nullable=True)
    lr_tire_wear_middle: Mapped[float | None] = mapped_column(Float, nullable=True)
    lr_tire_wear_right: Mapped[float | None] = mapped_column(Float, nullable=True)
    lr_brake_pressure: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Right Rear
    rr_tire_temp_left: Mapped[float | None] = mapped_column(Float, nullable=True)
    rr_tire_temp_middle: Mapped[float | None] = mapped_column(Float, nullable=True)
    rr_tire_temp_right: Mapped[float | None] = mapped_column(Float, nullable=True)
    rr_tire_wear_left: Mapped[float | None] = mapped_column(Float, nullable=True)
    rr_tire_wear_middle: Mapped[float | None] = mapped_column(Float, nullable=True)
    rr_tire_wear_right: Mapped[float | None] = mapped_column(Float, nullable=True)
    rr_brake_pressure: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Track conditions
    track_temp: Mapped[float | None] = mapped_column(Float, nullable=True)
    track_wetness: Mapped[int | None] = mapped_column(Integer, nullable=True)
    air_temp: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Session state
    session_flags: Mapped[int | None] = mapped_column(Integer, nullable=True)
    track_surface: Mapped[int | None] = mapped_column(Integer, nullable=True)
    on_pit_road: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default_factory=uuid.uuid4
    )

    # Relationships
    track_session: Mapped["TrackSession"] = relationship(
        "TrackSession", back_populates="telemetry_frames", init=False
    )
    lap: Mapped["Lap"] = relationship("Lap", back_populates="telemetry_frames", init=False)

    # Indexes for efficient time-series queries
    __table_args__ = (
        Index("idx_telemetry_lap_id", "lap_id"),
        Index("idx_telemetry_track_session_id", "track_session_id"),
        Index("idx_telemetry_timestamp", "timestamp"),
        Index("idx_session_time", "session_time"),
    )


class LapMetricsDB(Base):
    """Model representing aggregate metrics for a lap."""

    __tablename__ = "lap_metrics"

    # Non-default fields first
    lap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lap.id", ondelete="CASCADE"), nullable=False
    )

    # Lap-wide statistics (removed lap_number per user request)
    lap_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_corners: Mapped[int] = mapped_column(Integer, nullable=False)
    total_braking_zones: Mapped[int] = mapped_column(Integer, nullable=False)
    average_corner_speed: Mapped[float] = mapped_column(Float, nullable=False)
    max_speed: Mapped[float] = mapped_column(Float, nullable=False)
    min_speed: Mapped[float] = mapped_column(Float, nullable=False)

    # Fields with defaults come after
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default_factory=uuid.uuid4, init=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )

    # Relationships
    lap: Mapped["Lap"] = relationship("Lap", back_populates="metrics", init=False)
    braking_zones: Mapped[list["BrakingMetricsDB"]] = relationship(
        "BrakingMetricsDB",
        back_populates="lap_metrics",
        cascade="all, delete-orphan",
        init=False,
        order_by="BrakingMetricsDB.zone_number",
    )
    corners: Mapped[list["CornerMetricsDB"]] = relationship(
        "CornerMetricsDB",
        back_populates="lap_metrics",
        cascade="all, delete-orphan",
        init=False,
        order_by="CornerMetricsDB.corner_number",
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("lap_id", name="uq_lap_metrics_lap_id"),
        Index("idx_lap_metrics_lap_id", "lap_id"),
    )


class BrakingMetricsDB(Base):
    """Model representing metrics for a braking zone."""

    __tablename__ = "braking_metrics"

    # Non-default fields first
    lap_metrics_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lap_metrics.id", ondelete="CASCADE"),
        nullable=False,
    )
    zone_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Location and timing
    braking_point_distance: Mapped[float] = mapped_column(Float, nullable=False)
    braking_point_speed: Mapped[float] = mapped_column(Float, nullable=False)
    end_distance: Mapped[float] = mapped_column(Float, nullable=False)

    # Performance metrics
    max_brake_pressure: Mapped[float] = mapped_column(Float, nullable=False)
    braking_duration: Mapped[float] = mapped_column(Float, nullable=False)
    minimum_speed: Mapped[float] = mapped_column(Float, nullable=False)

    # Advanced metrics
    initial_deceleration: Mapped[float] = mapped_column(Float, nullable=False)
    average_deceleration: Mapped[float] = mapped_column(Float, nullable=False)
    braking_efficiency: Mapped[float] = mapped_column(Float, nullable=False)

    # Trail braking
    has_trail_braking: Mapped[bool] = mapped_column(Boolean, nullable=False)
    trail_brake_distance: Mapped[float] = mapped_column(Float, nullable=False)
    trail_brake_percentage: Mapped[float] = mapped_column(Float, nullable=False)

    # Fields with defaults come after
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default_factory=uuid.uuid4, init=False
    )

    # Relationship
    lap_metrics: Mapped["LapMetricsDB"] = relationship(
        "LapMetricsDB", back_populates="braking_zones", init=False
    )

    # Indexes
    __table_args__ = (
        Index("idx_braking_metrics_lap_metrics_id", "lap_metrics_id"),
        Index("idx_braking_metrics_zone_number", "lap_metrics_id", "zone_number"),
    )


class CornerMetricsDB(Base):
    """Model representing metrics for a corner."""

    __tablename__ = "corner_metrics"

    # Non-default fields first
    lap_metrics_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lap_metrics.id", ondelete="CASCADE"),
        nullable=False,
    )
    corner_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Key corner points (distances)
    turn_in_distance: Mapped[float] = mapped_column(Float, nullable=False)
    apex_distance: Mapped[float] = mapped_column(Float, nullable=False)
    exit_distance: Mapped[float] = mapped_column(Float, nullable=False)
    throttle_application_distance: Mapped[float] = mapped_column(Float, nullable=False)

    # Speeds at key points
    turn_in_speed: Mapped[float] = mapped_column(Float, nullable=False)
    apex_speed: Mapped[float] = mapped_column(Float, nullable=False)
    exit_speed: Mapped[float] = mapped_column(Float, nullable=False)
    throttle_application_speed: Mapped[float] = mapped_column(Float, nullable=False)

    # Performance metrics
    max_lateral_g: Mapped[float] = mapped_column(Float, nullable=False)
    time_in_corner: Mapped[float] = mapped_column(Float, nullable=False)
    corner_distance: Mapped[float] = mapped_column(Float, nullable=False)

    # Steering metrics
    max_steering_angle: Mapped[float] = mapped_column(Float, nullable=False)

    # Speed delta
    speed_loss: Mapped[float] = mapped_column(Float, nullable=False)
    speed_gain: Mapped[float] = mapped_column(Float, nullable=False)

    # Fields with defaults come after
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default_factory=uuid.uuid4, init=False
    )

    # Relationship
    lap_metrics: Mapped["LapMetricsDB"] = relationship(
        "LapMetricsDB", back_populates="corners", init=False
    )

    # Indexes
    __table_args__ = (
        Index("idx_corner_metrics_lap_metrics_id", "lap_metrics_id"),
        Index("idx_corner_metrics_corner_number", "lap_metrics_id", "corner_number"),
    )
