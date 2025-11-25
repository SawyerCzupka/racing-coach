"""Service for telemetry domain: sessions, laps, and telemetry data.

This service consolidates all business logic and data access for the telemetry feature,
eliminating the repository layer per the migration spec.
"""

import logging
from uuid import UUID

from racing_coach_core.algs.events import LapMetrics as LapMetricsDataclass
from racing_coach_core.models.telemetry import SessionFrame, TelemetrySequence
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from racing_coach_server.telemetry.exceptions import LapNotFoundError, SessionNotFoundError
from racing_coach_server.telemetry.models import (
    BrakingMetricsDB,
    CornerMetricsDB,
    Lap,
    LapMetricsDB,
    Telemetry,
    TrackSession,
)

logger = logging.getLogger(__name__)


class TelemetryService:
    """Service for telemetry domain: sessions, laps, and telemetry data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_or_get_session(self, session_frame: SessionFrame) -> TrackSession:
        """
        Idempotent session creation - returns existing session if found,
        creates new one otherwise.

        Args:
            session_frame: The session information from the client

        Returns:
            TrackSession: The existing or newly created session
        """
        # Check if session already exists by ID
        stmt = select(TrackSession).where(TrackSession.id == session_frame.session_id)
        result = await self.db.execute(stmt)
        existing_session = result.scalar_one_or_none()

        if existing_session:
            logger.debug(f"Found existing session with ID {session_frame.session_id}")
            return existing_session

        # Create new session
        new_session = TrackSession(
            id=session_frame.session_id,
            track_id=session_frame.track_id,
            track_name=session_frame.track_name,
            track_config_name=session_frame.track_config_name,
            track_type=session_frame.track_type,
            car_id=session_frame.car_id,
            car_name=session_frame.car_name,
            car_class_id=session_frame.car_class_id,
            series_id=session_frame.series_id,
        )
        self.db.add(new_session)
        await self.db.flush()  # Flush to ensure ID is available
        logger.info(f"Created new session with ID {new_session.id}")
        return new_session

    async def get_latest_session(self) -> TrackSession | None:
        """
        Get the most recent track session.

        Returns:
            TrackSession | None: The latest session or None if no sessions exist
        """
        stmt = select(TrackSession).order_by(desc(TrackSession.created_at)).limit(1)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            logger.debug(f"Found latest session with ID {session.id}")
        else:
            logger.debug("No sessions found in database")

        return session

    async def get_all_sessions(self) -> list[TrackSession]:
        """
        Get all track sessions ordered by created_at descending.

        Returns:
            list[TrackSession]: All sessions with their lap counts
        """
        stmt = (
            select(TrackSession)
            .options(selectinload(TrackSession.laps))
            .order_by(desc(TrackSession.created_at))
        )
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        logger.debug(f"Found {len(sessions)} sessions")
        return list(sessions)

    async def get_session_by_id(self, session_id: UUID) -> TrackSession | None:
        """
        Get a specific session by ID with its laps.

        Args:
            session_id: The ID of the session

        Returns:
            TrackSession | None: The session or None if not found
        """
        stmt = (
            select(TrackSession)
            .where(TrackSession.id == session_id)
            .options(selectinload(TrackSession.laps))
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            logger.debug(f"Found session with ID {session_id}")
        else:
            logger.debug(f"No session found with ID {session_id}")

        return session

    async def get_laps_for_session(self, session_id: UUID) -> list[Lap]:
        """
        Get all laps for a session ordered by lap number.

        Args:
            session_id: The ID of the session

        Returns:
            list[Lap]: The laps for the session
        """
        stmt = (
            select(Lap)
            .where(Lap.track_session_id == session_id)
            .options(selectinload(Lap.metrics))
            .order_by(Lap.lap_number)
        )
        result = await self.db.execute(stmt)
        laps = result.scalars().all()

        logger.debug(f"Found {len(laps)} laps for session {session_id}")
        return list(laps)

    async def get_lap_by_id(self, lap_id: UUID) -> Lap | None:
        """
        Get a specific lap by ID with its metrics.

        Args:
            lap_id: The ID of the lap

        Returns:
            Lap | None: The lap or None if not found
        """
        stmt = (
            select(Lap)
            .where(Lap.id == lap_id)
            .options(
                selectinload(Lap.metrics).selectinload(LapMetricsDB.braking_zones),
                selectinload(Lap.metrics).selectinload(LapMetricsDB.corners),
                selectinload(Lap.track_session),
            )
        )
        result = await self.db.execute(stmt)
        lap = result.scalar_one_or_none()

        if lap:
            logger.debug(f"Found lap with ID {lap_id}")
        else:
            logger.debug(f"No lap found with ID {lap_id}")

        return lap

    async def add_lap(
        self,
        track_session_id: UUID,
        lap_number: int,
        lap_time: float | None = None,
        is_valid: bool = False,
    ) -> Lap:
        """
        Create a lap record for a session.

        Args:
            track_session_id: The ID of the track session
            lap_number: The lap number
            lap_time: Optional lap time (nullable)
            is_valid: Whether the lap is valid

        Returns:
            Lap: The created lap record
        """
        lap = Lap(
            track_session_id=track_session_id,
            lap_number=lap_number,
            lap_time=lap_time,
            is_valid=is_valid,
        )
        self.db.add(lap)
        await self.db.flush()  # Flush to get the ID
        logger.info(f"Created lap {lap_number} for session {track_session_id}")
        return lap

    async def add_telemetry_sequence(
        self,
        telemetry_sequence: TelemetrySequence,
        lap_id: UUID,
        session_id: UUID,
    ) -> None:
        """
        Batch insert telemetry frames for a lap.

        Args:
            telemetry_sequence: The sequence of telemetry frames to add
            lap_id: The ID of the lap
            session_id: The ID of the session
        """
        frames: list[Telemetry] = []
        for frame in telemetry_sequence.frames:
            # Extract tire data from nested dictionaries
            tire_temps = frame.tire_temps
            tire_wear = frame.tire_wear
            brake_pressure = frame.brake_line_pressure

            telemetry = Telemetry(
                track_session_id=session_id,
                lap_id=lap_id,
                timestamp=frame.timestamp,
                session_time=frame.session_time,
                lap_number=frame.lap_number,
                lap_distance_pct=frame.lap_distance_pct,
                lap_distance=frame.lap_distance,
                current_lap_time=frame.current_lap_time,
                last_lap_time=frame.last_lap_time,
                best_lap_time=frame.best_lap_time,
                speed=frame.speed,
                rpm=frame.rpm,
                gear=frame.gear,
                throttle=frame.throttle,
                brake=frame.brake,
                clutch=frame.clutch,
                steering_angle=frame.steering_angle,
                lateral_acceleration=frame.lateral_acceleration,
                longitudinal_acceleration=frame.longitudinal_acceleration,
                vertical_acceleration=frame.vertical_acceleration,
                yaw_rate=frame.yaw_rate,
                roll_rate=frame.roll_rate,
                pitch_rate=frame.pitch_rate,
                velocity_x=frame.velocity_x,
                velocity_y=frame.velocity_y,
                velocity_z=frame.velocity_z,
                yaw=frame.yaw,
                pitch=frame.pitch,
                roll=frame.roll,
                latitude=frame.latitude,
                longitude=frame.longitude,
                altitude=frame.altitude,
                track_temp=frame.track_temp,
                track_wetness=frame.track_wetness,
                air_temp=frame.air_temp,
                session_flags=frame.session_flags,
                track_surface=frame.track_surface,
                on_pit_road=frame.on_pit_road,
                # Flatten tire data
                lf_tire_temp_left=tire_temps["LF"]["left"],
                lf_tire_temp_middle=tire_temps["LF"]["middle"],
                lf_tire_temp_right=tire_temps["LF"]["right"],
                rf_tire_temp_left=tire_temps["RF"]["left"],
                rf_tire_temp_middle=tire_temps["RF"]["middle"],
                rf_tire_temp_right=tire_temps["RF"]["right"],
                lr_tire_temp_left=tire_temps["LR"]["left"],
                lr_tire_temp_middle=tire_temps["LR"]["middle"],
                lr_tire_temp_right=tire_temps["LR"]["right"],
                rr_tire_temp_left=tire_temps["RR"]["left"],
                rr_tire_temp_middle=tire_temps["RR"]["middle"],
                rr_tire_temp_right=tire_temps["RR"]["right"],
                lf_tire_wear_left=tire_wear["LF"]["left"],
                lf_tire_wear_middle=tire_wear["LF"]["middle"],
                lf_tire_wear_right=tire_wear["LF"]["right"],
                rf_tire_wear_left=tire_wear["RF"]["left"],
                rf_tire_wear_middle=tire_wear["RF"]["middle"],
                rf_tire_wear_right=tire_wear["RF"]["right"],
                lr_tire_wear_left=tire_wear["LR"]["left"],
                lr_tire_wear_middle=tire_wear["LR"]["middle"],
                lr_tire_wear_right=tire_wear["LR"]["right"],
                rr_tire_wear_left=tire_wear["RR"]["left"],
                rr_tire_wear_middle=tire_wear["RR"]["middle"],
                rr_tire_wear_right=tire_wear["RR"]["right"],
                lf_brake_pressure=brake_pressure["LF"],
                rf_brake_pressure=brake_pressure["RF"],
                lr_brake_pressure=brake_pressure["LR"],
                rr_brake_pressure=brake_pressure["RR"],
            )
            frames.append(telemetry)

        self.db.add_all(frames)
        logger.info(f"Added {len(frames)} telemetry frames for lap {lap_id}")

    async def add_or_update_lap_metrics(
        self,
        lap_metrics: LapMetricsDataclass,
        lap_id: UUID,
    ) -> LapMetricsDB:
        """
        Add or update metrics for a lap (upsert pattern).

        If metrics already exist for this lap, they are deleted and replaced.

        Args:
            lap_metrics: The metrics dataclass from the core library
            lap_id: The ID of the lap

        Returns:
            LapMetricsDB: The created metrics record

        Raises:
            LapNotFoundError: If the lap does not exist
        """
        # Verify lap exists
        stmt = select(Lap).where(Lap.id == lap_id)
        result = await self.db.execute(stmt)
        lap = result.scalar_one_or_none()

        if not lap:
            raise LapNotFoundError(f"Lap with ID {lap_id} not found")

        # Delete existing metrics if they exist (upsert pattern)
        delete_stmt = delete(LapMetricsDB).where(LapMetricsDB.lap_id == lap_id)
        await self.db.execute(delete_stmt)
        await self.db.flush()

        # Create new metrics record
        db_lap_metrics = LapMetricsDB(
            lap_id=lap_id,
            lap_time=lap_metrics.lap_time,
            total_corners=lap_metrics.total_corners,
            total_braking_zones=lap_metrics.total_braking_zones,
            average_corner_speed=lap_metrics.average_corner_speed,
            max_speed=lap_metrics.max_speed,
            min_speed=lap_metrics.min_speed,
        )
        self.db.add(db_lap_metrics)
        await self.db.flush()  # Flush to get the ID

        # Create braking zone records
        braking_zones: list[BrakingMetricsDB] = []
        for i, braking in enumerate(lap_metrics.braking_zones, start=1):
            db_braking = BrakingMetricsDB(
                lap_metrics_id=db_lap_metrics.id,
                zone_number=i,
                braking_point_distance=braking.braking_point_distance,
                braking_point_speed=braking.braking_point_speed,
                end_distance=braking.end_distance,
                max_brake_pressure=braking.max_brake_pressure,
                braking_duration=braking.braking_duration,
                minimum_speed=braking.minimum_speed,
                initial_deceleration=braking.initial_deceleration,
                average_deceleration=braking.average_deceleration,
                braking_efficiency=braking.braking_efficiency,
                has_trail_braking=braking.has_trail_braking,
                trail_brake_distance=braking.trail_brake_distance,
                trail_brake_percentage=braking.trail_brake_percentage,
            )
            braking_zones.append(db_braking)

        # Create corner records
        corners: list[CornerMetricsDB] = []
        for i, corner in enumerate(lap_metrics.corners, start=1):
            db_corner = CornerMetricsDB(
                lap_metrics_id=db_lap_metrics.id,
                corner_number=i,
                turn_in_distance=corner.turn_in_distance,
                apex_distance=corner.apex_distance,
                exit_distance=corner.exit_distance,
                throttle_application_distance=corner.throttle_application_distance,
                turn_in_speed=corner.turn_in_speed,
                apex_speed=corner.apex_speed,
                exit_speed=corner.exit_speed,
                throttle_application_speed=corner.throttle_application_speed,
                max_lateral_g=corner.max_lateral_g,
                time_in_corner=corner.time_in_corner,
                corner_distance=corner.corner_distance,
                max_steering_angle=corner.max_steering_angle,
                speed_loss=corner.speed_loss,
                speed_gain=corner.speed_gain,
            )
            corners.append(db_corner)

        # Batch insert
        self.db.add_all(braking_zones)
        self.db.add_all(corners)

        logger.info(
            f"Added/updated metrics for lap {lap_id}: "
            f"{len(braking_zones)} braking zones, {len(corners)} corners"
        )

        return db_lap_metrics

    async def get_lap_metrics(self, lap_id: UUID) -> LapMetricsDB | None:
        """
        Get metrics for a specific lap.

        Args:
            lap_id: The ID of the lap

        Returns:
            LapMetricsDB | None: The metrics record with relationships loaded, or None
        """
        stmt = (
            select(LapMetricsDB)
            .where(LapMetricsDB.lap_id == lap_id)
            .options(
                selectinload(LapMetricsDB.braking_zones),
                selectinload(LapMetricsDB.corners),
            )
        )
        result = await self.db.execute(stmt)
        metrics = result.scalar_one_or_none()

        if metrics:
            logger.debug(f"Found metrics for lap {lap_id}")
        else:
            logger.debug(f"No metrics found for lap {lap_id}")

        return metrics

    async def get_telemetry_for_lap(self, lap_id: UUID) -> list[Telemetry]:
        """
        Get all telemetry frames for a specific lap, ordered by session time.

        Args:
            lap_id: The ID of the lap

        Returns:
            list[Telemetry]: The telemetry frames for the lap
        """
        stmt = (
            select(Telemetry)
            .where(Telemetry.lap_id == lap_id)
            .order_by(Telemetry.session_time)
        )
        result = await self.db.execute(stmt)
        frames = result.scalars().all()

        logger.debug(f"Found {len(frames)} telemetry frames for lap {lap_id}")
        return list(frames)
