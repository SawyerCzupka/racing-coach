import logging
import uuid

from racing_coach_core.models.telemetry import TelemetryFrame

from ..models import Telemetry
from .base import BaseRepository

logger = logging.getLogger(__name__)


class TelemetryRepository(BaseRepository):
    """Repository for managing telemetry data."""

    def create_from_telemetry_frame(
        self, telemetry_frame: TelemetryFrame, session_id: uuid.UUID, lap_id: uuid.UUID
    ) -> Telemetry:
        """Create a new telemetry record from a TelemetryFrame object."""
        # Extract tire data from nested dictionaries
        tire_temps = telemetry_frame.tire_temps
        tire_wear = telemetry_frame.tire_wear
        brake_pressure = telemetry_frame.brake_line_pressure

        telemetry = Telemetry(
            session_id=session_id,
            lap_id=lap_id,
            timestamp=telemetry_frame.timestamp,
            session_time=telemetry_frame.session_time,
            lap_number=telemetry_frame.lap_number,
            lap_distance_pct=telemetry_frame.lap_distance_pct,
            lap_distance=telemetry_frame.lap_distance,
            current_lap_time=telemetry_frame.current_lap_time,
            last_lap_time=telemetry_frame.last_lap_time,
            best_lap_time=telemetry_frame.best_lap_time,
            speed=telemetry_frame.speed,
            rpm=telemetry_frame.rpm,
            gear=telemetry_frame.gear,
            throttle=telemetry_frame.throttle,
            brake=telemetry_frame.brake,
            clutch=telemetry_frame.clutch,
            steering_angle=telemetry_frame.steering_angle,
            lateral_acceleration=telemetry_frame.lateral_acceleration,
            longitudinal_acceleration=telemetry_frame.longitudinal_acceleration,
            vertical_acceleration=telemetry_frame.vertical_acceleration,
            yaw_rate=telemetry_frame.yaw_rate,
            roll_rate=telemetry_frame.roll_rate,
            pitch_rate=telemetry_frame.pitch_rate,
            position_x=telemetry_frame.position_x,
            position_y=telemetry_frame.position_y,
            position_z=telemetry_frame.position_z,
            yaw=telemetry_frame.yaw,
            pitch=telemetry_frame.pitch,
            roll=telemetry_frame.roll,
            track_temp=telemetry_frame.track_temp,
            track_wetness=telemetry_frame.track_wetness,
            air_temp=telemetry_frame.air_temp,
            session_flags=telemetry_frame.session_flags,
            track_surface=telemetry_frame.track_surface,
            on_pit_road=telemetry_frame.on_pit_road,
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

        self.db_session.add(telemetry)
        # self.db_session.commit()

        return telemetry
