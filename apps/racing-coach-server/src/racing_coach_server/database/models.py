"""SQLAlchemy models for the Racing Coach database."""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import (
    relationship,
    Mapped,
    mapped_column,
    DeclarativeBase,
    MappedAsDataclass,
)

# from .database import Base


class Base(MappedAsDataclass, DeclarativeBase):
    """Base class for all SQLAlchemy models."""


class TrackSession(Base):
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


class Lap(Base):
    """Model representing a lap in a session."""

    __tablename__ = "lap"

    track_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("track_session.id", ondelete="CASCADE"),
        nullable=False,
    )
    lap_number: Mapped[int] = mapped_column(Integer, nullable=False)
    lap_time: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # May be null if lap is not completed
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
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint(
            "track_session_id", "lap_number", name="uq_track_session_id_lap_number"
        ),
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
    )  # Global timestamp for telemetry data
    session_time: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Timestamp as reported by iRacing

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
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )  # TODO: Consider removing this

    # Relationships
    track_session: Mapped["TrackSession"] = relationship(
        "TrackSession", back_populates="telemetry_frames", init=False
    )
    lap: Mapped["Lap"] = relationship(
        "Lap", back_populates="telemetry_frames", init=False
    )

    # Indexes for efficient time-series queries
    __table_args__ = (
        Index("idx_telemetry_lap_id", "lap_id"),
        Index("idx_telemetry_track_session_id", "track_session_id"),
        Index("idx_telemetry_timestamp", "timestamp"),
        Index("idx_session_time", "session_time"),
    )
