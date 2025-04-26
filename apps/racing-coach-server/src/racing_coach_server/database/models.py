"""SQLAlchemy models for the Racing Coach database."""

from datetime import datetime
import uuid
from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    func,
    Text,
    JSON,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Session(Base):
    __tablename__ = "session"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    track_id = Column(Integer, nullable=False)
    track_name = Column(String(255), nullable=False)
    track_config_name = Column(String(255), nullable=True)
    track_type = Column(String(50), nullable=False)
    car_id = Column(Integer, nullable=False)
    car_name = Column(String(255), nullable=False)
    car_class_id = Column(Integer, nullable=False)
    series_id = Column(Integer, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    laps = relationship("Lap", back_populates="session", cascade="all, delete-orphan")
    telemetry_frames = relationship(
        "Telemetry", back_populates="session", cascade="all, delete-orphan"
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("session.id", ondelete="CASCADE"), nullable=False
    )
    lap_number = Column(Integer, nullable=False)
    lap_time = Column(Float, nullable=True)  # May be null if lap is not completed
    is_valid = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    session = relationship("Session", back_populates="laps")
    telemetry_frames = relationship(
        "Telemetry", back_populates="lap", cascade="all, delete-orphan"
    )

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint("session_id", "lap_number", name="uq_session_lap_number"),
        Index("idx_lap_session_number", "session_id", "lap_number"),
    )


class Telemetry(Base):
    """Model representing a telemetry frame."""

    __tablename__ = "telemetry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("session.id", ondelete="CASCADE"), nullable=False
    )
    lap_id = Column(
        UUID(as_uuid=True), ForeignKey("lap.id", ondelete="CASCADE"), nullable=False
    )

    # Time fields
    timestamp = Column(
        DateTime(timezone=True),
        primary_key=True,
        server_default=func.now(),
        nullable=False,
    )
    session_time = Column(Float, nullable=False)

    # Lap information
    lap_number = Column(Integer, nullable=False)
    lap_distance_pct = Column(Float, nullable=False)
    lap_distance = Column(Float, nullable=False)
    current_lap_time = Column(Float, nullable=False)
    last_lap_time = Column(Float, nullable=True)
    best_lap_time = Column(Float, nullable=True)

    # Vehicle state
    speed = Column(Float, nullable=False)
    rpm = Column(Float, nullable=False)
    gear = Column(Integer, nullable=False)

    # Driver inputs
    throttle = Column(Float, nullable=False)
    brake = Column(Float, nullable=False)
    clutch = Column(Float, nullable=False)
    steering_angle = Column(Float, nullable=False)

    # Vehicle dynamics
    lateral_acceleration = Column(Float, nullable=False)
    longitudinal_acceleration = Column(Float, nullable=False)
    vertical_acceleration = Column(Float, nullable=False)
    yaw_rate = Column(Float, nullable=False)
    roll_rate = Column(Float, nullable=False)
    pitch_rate = Column(Float, nullable=False)

    # Vehicle position/orientation
    position_x = Column(Float, nullable=False)
    position_y = Column(Float, nullable=False)
    position_z = Column(Float, nullable=False)
    yaw = Column(Float, nullable=False)
    pitch = Column(Float, nullable=False)
    roll = Column(Float, nullable=False)

    # Tire data - flattened for better query performance
    # Left Front
    lf_tire_temp_left = Column(Float, nullable=True)
    lf_tire_temp_middle = Column(Float, nullable=True)
    lf_tire_temp_right = Column(Float, nullable=True)
    lf_tire_wear_left = Column(Float, nullable=True)
    lf_tire_wear_middle = Column(Float, nullable=True)
    lf_tire_wear_right = Column(Float, nullable=True)
    lf_brake_pressure = Column(Float, nullable=True)

    # Right Front
    rf_tire_temp_left = Column(Float, nullable=True)
    rf_tire_temp_middle = Column(Float, nullable=True)
    rf_tire_temp_right = Column(Float, nullable=True)
    rf_tire_wear_left = Column(Float, nullable=True)
    rf_tire_wear_middle = Column(Float, nullable=True)
    rf_tire_wear_right = Column(Float, nullable=True)
    rf_brake_pressure = Column(Float, nullable=True)

    # Left Rear
    lr_tire_temp_left = Column(Float, nullable=True)
    lr_tire_temp_middle = Column(Float, nullable=True)
    lr_tire_temp_right = Column(Float, nullable=True)
    lr_tire_wear_left = Column(Float, nullable=True)
    lr_tire_wear_middle = Column(Float, nullable=True)
    lr_tire_wear_right = Column(Float, nullable=True)
    lr_brake_pressure = Column(Float, nullable=True)

    # Right Rear
    rr_tire_temp_left = Column(Float, nullable=True)
    rr_tire_temp_middle = Column(Float, nullable=True)
    rr_tire_temp_right = Column(Float, nullable=True)
    rr_tire_wear_left = Column(Float, nullable=True)
    rr_tire_wear_middle = Column(Float, nullable=True)
    rr_tire_wear_right = Column(Float, nullable=True)
    rr_brake_pressure = Column(Float, nullable=True)

    # Track conditions
    track_temp = Column(Float, nullable=True)
    track_wetness = Column(Integer, nullable=True)
    air_temp = Column(Float, nullable=True)

    # Session state
    session_flags = Column(Integer, nullable=True)
    track_surface = Column(Integer, nullable=True)
    on_pit_road = Column(Boolean, nullable=True)

    # Relationships
    session = relationship("Session", back_populates="telemetry_frames")
    lap = relationship("Lap", back_populates="telemetry_frames")

    # Indexes for efficient time-series queries
    __table_args__ = (
        Index("idx_telemetry_lap_id", "lap_id"),
        Index("idx_telemetry_session_id", "session_id"),
        Index("idx_telemetry_timestamp", "timestamp"),
    )
