"""
TimescaleDB connector for storing and retrieving racing telemetry data.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import sqlalchemy as sa
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from racing_coach.core.schema.telemetry import (
    LapTelemetry,
    SessionFrame,
    TelemetryFrame,
)
from racing_coach.core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

Base = declarative_base()


class Session(Base):
    """Represents a racing session in the database."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    track_id = Column(Integer, nullable=False)
    track_name = Column(String, nullable=False)
    track_config_name = Column(String, nullable=True)
    track_type = Column(String, nullable=False)
    car_id = Column(Integer, nullable=False)
    car_name = Column(String, nullable=False)
    car_class_id = Column(Integer, nullable=False)
    series_id = Column(Integer, nullable=False)
    # session_type = Column(String, nullable=False)

    # Relationships
    laps = relationship("Lap", back_populates="session", cascade="all, delete-orphan")

    @classmethod
    def from_session_frame(cls, frame: SessionFrame) -> "Session":
        """Create a Session object from a SessionFrame."""
        return cls(
            timestamp=frame.timestamp,
            track_id=frame.track_id,
            track_name=frame.track_name,
            track_config_name=frame.track_config_name,
            track_type=frame.track_type,
            car_id=frame.car_id,
            car_name=frame.car_name,
            car_class_id=frame.car_class_id,
            series_id=frame.series_id,
            # session_type=frame.session_type,
        )


class Lap(Base):
    """Represents a single lap in the database."""

    __tablename__ = "laps"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    lap_number = Column(Integer, nullable=False)
    lap_time = Column(Float, nullable=True)
    is_valid = Column(Boolean, default=True)
    timestamp_start = Column(DateTime, nullable=False)
    timestamp_end = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("Session", back_populates="laps")
    telemetry = relationship(
        "Telemetry", back_populates="lap", cascade="all, delete-orphan"
    )

    @classmethod
    def from_lap_telemetry(cls, lap: LapTelemetry, session_id: int) -> "Lap":
        """Create a Lap object from a LapTelemetry."""
        if not lap.frames:
            raise ValueError("Lap has no frames")

        lap_number = lap.frames[0].lap_number
        is_valid, _ = lap.is_valid()

        return cls(
            session_id=session_id,
            lap_number=lap_number,
            lap_time=lap.lap_time or lap.get_lap_time(),
            is_valid=is_valid,
            timestamp_start=lap.frames[0].timestamp,
            timestamp_end=lap.frames[-1].timestamp if len(lap.frames) > 1 else None,
        )


class Telemetry(Base):
    """Represents telemetry data points in the database."""

    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lap_id = Column(Integer, ForeignKey("laps.id"))
    timestamp = Column(DateTime, nullable=False, primary_key=True)
    session_time = Column(Float, nullable=False)
    lap_distance_pct = Column(Float, nullable=False)
    lap_distance = Column(Float, nullable=False)
    speed = Column(Float, nullable=False)
    rpm = Column(Float, nullable=False)
    gear = Column(Integer, nullable=False)
    throttle = Column(Float, nullable=False)
    brake = Column(Float, nullable=False)
    clutch = Column(Float, nullable=False)
    steering_angle = Column(Float, nullable=False)
    lateral_acceleration = Column(Float, nullable=False)
    longitudinal_acceleration = Column(Float, nullable=False)
    yaw_rate = Column(Float, nullable=False)

    # Store complex data as JSON
    tire_temps = Column(JSONB, nullable=False)
    tire_wear = Column(JSONB, nullable=False)
    brake_line_pressure = Column(JSONB, nullable=False)

    # Track conditions
    track_temp = Column(Float, nullable=False)
    air_temp = Column(Float, nullable=False)

    # Additional data stored as JSON to avoid too many columns
    extended_data = Column(JSONB, nullable=True)

    # Relationship
    lap = relationship("Lap", back_populates="telemetry")

    @classmethod
    def from_telemetry_frame(cls, frame: TelemetryFrame, lap_id: int) -> "Telemetry":
        """Create a Telemetry object from a TelemetryFrame."""
        # Store less frequently used fields in extended_data
        extended_data = {
            "current_lap_time": frame.current_lap_time,
            "last_lap_time": frame.last_lap_time,
            "best_lap_time": frame.best_lap_time,
            "vertical_acceleration": frame.vertical_acceleration,
            "roll_rate": frame.roll_rate,
            "pitch_rate": frame.pitch_rate,
            "position_x": frame.position_x,
            "position_y": frame.position_y,
            "position_z": frame.position_z,
            "yaw": frame.yaw,
            "pitch": frame.pitch,
            "roll": frame.roll,
            "track_wetness": frame.track_wetness,
            "session_flags": frame.session_flags,
            "track_surface": frame.track_surface,
            "on_pit_road": frame.on_pit_road,
        }

        return cls(
            lap_id=lap_id,
            timestamp=frame.timestamp,
            session_time=frame.session_time,
            lap_distance_pct=frame.lap_distance_pct,
            lap_distance=frame.lap_distance,
            speed=frame.speed,
            rpm=frame.rpm,
            gear=frame.gear,
            throttle=frame.throttle,
            brake=frame.brake,
            clutch=frame.clutch,
            steering_angle=frame.steering_angle,
            lateral_acceleration=frame.lateral_acceleration,
            longitudinal_acceleration=frame.longitudinal_acceleration,
            yaw_rate=frame.yaw_rate,
            tire_temps=frame.tire_temps,
            tire_wear=frame.tire_wear,
            brake_line_pressure=frame.brake_line_pressure,
            track_temp=frame.track_temp,
            air_temp=frame.air_temp,
            extended_data=extended_data,
        )


class DatabaseManager:
    """Manages database connections and operations for the racing coach."""

    def __init__(
        self, connection_string: Optional[str] = None, force_recreate: bool = False
    ):
        """Initialize the database manager.

        Args:
            connection_string: SQLAlchemy connection string for the TimescaleDB database.
                If None, uses the connection string from settings.
        """
        self.connection_string = connection_string or settings.DB_CONNECTION_STRING
        self.engine = sa.create_engine(self.connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self._current_session_id: Optional[int] = None
        self._force_recreate: bool = force_recreate

        if self._force_recreate:
            self.initialize_database()

    def initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        # Create tables

        if self._force_recreate:
            Base.metadata.drop_all(self.engine)

        Base.metadata.create_all(self.engine)

        # Convert telemetry table to TimescaleDB hypertable
        try:
            with self.engine.connect() as conn:
                # Check if TimescaleDB extension is installed
                conn.execute(
                    sa.text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
                )

                # Convert telemetry table to hypertable
                conn.execute(
                    sa.text(
                        "SELECT create_hypertable('telemetry', 'timestamp', if_not_exists => TRUE);"
                    )
                )
        except Exception as e:
            logger.error(f"Failed to create hypertable: {e}")

    def start_session(self, session_frame: SessionFrame) -> int:
        """Start a new racing session and return its ID."""
        db_session = Session.from_session_frame(session_frame)

        with self.Session() as session:
            session.add(db_session)
            session.commit()
            self._current_session_id = db_session.id  # type: ignore

        logger.info(
            f"Started new session {self._current_session_id}: {session_frame.track_name} - {session_frame.car_name}"
        )
        return self._current_session_id  # type: ignore

    def save_lap(self, lap_telemetry: LapTelemetry) -> int:
        """Save a completed lap and its telemetry data."""
        if not self._current_session_id:
            raise ValueError("No active session. Call start_session first.")

        with self.Session() as session:
            # Create lap record
            lap = Lap.from_lap_telemetry(lap_telemetry, self._current_session_id)
            session.add(lap)
            session.flush()  # Get the lap ID without committing

            # Create telemetry records
            for frame in lap_telemetry.frames:
                telemetry = Telemetry.from_telemetry_frame(
                    frame, lap.id
                )  # Ensure lap.id is flushed and contains the actual integer value
                session.add(telemetry)

            session.commit()
            logger.info(
                f"Saved lap {lap.lap_number} with {len(lap_telemetry.frames)} telemetry frames"
            )
            return lap.id

    def save_telemetry_frame(self, frame: TelemetryFrame) -> None:
        """Save a single telemetry frame for the current lap.

        This is used during active laps, before lap completion.
        """
        # Find or create lap for this frame
        if not self._current_session_id:
            raise ValueError("No active session. Call start_session first.")

        with self.Session() as session:
            # Look for existing lap
            lap = (
                session.query(Lap)
                .filter(
                    Lap.session_id == self._current_session_id,
                    Lap.lap_number == frame.lap_number,
                )
                .first()
            )

            # Create lap if it doesn't exist
            if not lap:
                lap = Lap(
                    session_id=self._current_session_id,
                    lap_number=frame.lap_number,
                    timestamp_start=frame.timestamp,
                    is_valid=True,  # Assume valid until proven otherwise
                )
                session.add(lap)
                session.flush()
            else:
                # Update timestamp_end
                lap.timestamp_end = frame.timestamp

            # Add telemetry
            telemetry = Telemetry.from_telemetry_frame(frame, lap.id)
            session.add(telemetry)
            session.commit()

    def save_telemetry_frame_batch(self, frames: List[TelemetryFrame]) -> None:
        """Save a batch of telemetry frames for the current lap."""
        if not self._current_session_id:
            raise ValueError("No active session. Call start_session first.")

        with self.Session() as session:
            # Find or create lap for each frame
            lap_dict = {}
            for frame in frames:
                if frame.lap_number not in lap_dict:
                    lap = (
                        session.query(Lap)
                        .filter(
                            Lap.session_id == self._current_session_id,
                            Lap.lap_number == frame.lap_number,
                        )
                        .first()
                    )
                    if not lap:
                        lap = Lap(
                            session_id=self._current_session_id,
                            lap_number=frame.lap_number,
                            timestamp_start=frame.timestamp,
                            is_valid=True,  # Assume valid until proven otherwise
                        )
                        session.add(lap)
                        session.flush()
                    lap_dict[frame.lap_number] = lap
                else:
                    lap = lap_dict[frame.lap_number]
                    lap.timestamp_end = frame.timestamp

                # Add telemetry
                telemetry = Telemetry.from_telemetry_frame(frame, lap.id)
                session.add(telemetry)

            session.commit()
            logger.info(f"Saved {len(frames)} telemetry frames")

    def get_sessions(
        self, track_name: Optional[str] = None, car_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get sessions matching the filters."""
        with self.Session() as session:
            query = session.query(Session)

            if track_name:
                query = query.filter(Session.track_name.ilike(f"%{track_name}%"))

            if car_name:
                query = query.filter(Session.car_name.ilike(f"%{car_name}%"))

            sessions = query.order_by(Session.timestamp.desc()).all()
            return [
                {
                    "id": s.id,
                    "timestamp": s.timestamp,
                    "track_name": s.track_name,
                    "track_config_name": s.track_config_name,
                    "car_name": s.car_name,
                    "session_type": s.session_type,
                }
                for s in sessions
            ]

    def get_laps(self, session_id: int) -> List[Dict[str, Any]]:
        """Get all laps for a session."""
        with self.Session() as session:
            laps = (
                session.query(Lap)
                .filter(Lap.session_id == session_id)
                .order_by(Lap.lap_number)
                .all()
            )
            return [
                {
                    "id": lap.id,
                    "lap_number": lap.lap_number,
                    "lap_time": lap.lap_time,
                    "is_valid": lap.is_valid,
                    "timestamp_start": lap.timestamp_start,
                    "timestamp_end": lap.timestamp_end,
                }
                for lap in laps
            ]

    def get_lap_telemetry(self, lap_id: int) -> LapTelemetry:
        """Retrieve telemetry data for a specific lap."""
        with self.Session() as session:
            lap = session.query(Lap).get(lap_id)
            if not lap:
                raise ValueError(f"Lap with ID {lap_id} not found")

            telemetry_data = (
                session.query(Telemetry)
                .filter(Telemetry.lap_id == lap_id)
                .order_by(Telemetry.timestamp)
                .all()
            )

            # Convert to TelemetryFrame objects
            frames = []
            for td in telemetry_data:
                # Create a dictionary with basic telemetry data
                frame_data = {
                    "timestamp": td.timestamp,
                    "session_time": td.session_time,
                    "lap_number": lap.lap_number,
                    "lap_distance_pct": td.lap_distance_pct,
                    "lap_distance": td.lap_distance,
                    "speed": td.speed,
                    "rpm": td.rpm,
                    "gear": td.gear,
                    "throttle": td.throttle,
                    "brake": td.brake,
                    "clutch": td.clutch,
                    "steering_angle": td.steering_angle,
                    "lateral_acceleration": td.lateral_acceleration,
                    "longitudinal_acceleration": td.longitudinal_acceleration,
                    "yaw_rate": td.yaw_rate,
                    "tire_temps": td.tire_temps,
                    "tire_wear": td.tire_wear,
                    "brake_line_pressure": td.brake_line_pressure,
                    "track_temp": td.track_temp,
                    "air_temp": td.air_temp,
                }

                # # Add extended data
                # if td.extended_data:
                #     frame_data.update(td.extended_data)

                frames.append(TelemetryFrame(**frame_data))

            return LapTelemetry(frames=frames, lap_time=lap.lap_time)

    def get_laps_by_track_car(
        self, track_name: str, car_name: str
    ) -> List[Tuple[int, int, float]]:
        """Get all lap IDs, lap numbers, and lap times for a specific track and car combination."""
        with self.Session() as session:
            # Join sessions and laps
            results = (
                session.query(Lap.id, Lap.lap_number, Lap.lap_time)
                .join(Session, Session.id == Lap.session_id)
                .filter(
                    Session.track_name.ilike(f"%{track_name}%"),
                    Session.car_name.ilike(f"%{car_name}%"),
                    Lap.is_valid == True,
                )
                .order_by(Lap.lap_time)
                .all()
            )
            return [
                (lap_id, lap_number, lap_time)
                for lap_id, lap_number, lap_time in results
            ]

    def get_fastest_lap(
        self, track_name: str, car_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get the fastest valid lap for a specific track and car combination."""
        with self.Session() as session:
            result = (
                session.query(
                    Lap.id,
                    Lap.lap_number,
                    Lap.lap_time,
                    Session.track_name,
                    Session.car_name,
                    Session.timestamp.label("session_date"),
                )
                .join(Session, Session.id == Lap.session_id)
                .filter(
                    Session.track_name.ilike(f"%{track_name}%"),
                    Session.car_name.ilike(f"%{car_name}%"),
                    Lap.is_valid == True,
                    Lap.lap_time.isnot(None),
                )
                .order_by(Lap.lap_time)
                .first()
            )

            if not result:
                return None

            return {
                "lap_id": result.id,
                "lap_number": result.lap_number,
                "lap_time": result.lap_time,
                "track_name": result.track_name,
                "car_name": result.car_name,
                "session_date": result.session_date,
            }
