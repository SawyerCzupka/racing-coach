"""Service for telemetry data management."""

import logging
from uuid import UUID

from racing_coach_core.schemas.telemetry import TelemetrySequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from racing_coach_server.telemetry.models import Telemetry

logger = logging.getLogger(__name__)


class TelemetryDataService:
    """Service for telemetry frame data operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

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

    async def get_telemetry_for_lap(self, lap_id: UUID) -> list[Telemetry]:
        """
        Get all telemetry frames for a specific lap, ordered by session time.

        Args:
            lap_id: The ID of the lap

        Returns:
            list[Telemetry]: The telemetry frames for the lap
        """
        stmt = select(Telemetry).where(Telemetry.lap_id == lap_id).order_by(Telemetry.session_time)
        result = await self.db.execute(stmt)
        frames = result.scalars().all()

        logger.debug(f"Found {len(frames)} telemetry frames for lap {lap_id}")
        return list(frames)
