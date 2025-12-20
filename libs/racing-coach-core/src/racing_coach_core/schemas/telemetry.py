import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, Self, runtime_checkable
from uuid import UUID, uuid4

import pandas as pd
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


@runtime_checkable
class TelemetryDataSource(Protocol):
    """
    Protocol for objects that provide telemetry data.

    This protocol defines the interface for reading telemetry variables,
    allowing the models to work with both live iRacing SDK instances and
    recorded IBT file readers.
    """

    def __getitem__(self, key: str) -> object:
        """Get a telemetry variable by name."""
        ...


class TelemetryFrame(BaseModel):
    """A single frame of driving telemetry data."""

    # Time
    timestamp: datetime = Field(
        description="Timestamp of the telemetry frame",
        default_factory=lambda: datetime.now(),
    )
    session_time: float = Field(description="Seconds since session start")

    # Lap Information
    lap_number: int = Field(description="Current lap number")
    lap_distance_pct: float = Field(description="Percentage of the lap completed")
    lap_distance: float = Field(description="Meters traveled from S/F this lap")
    current_lap_time: float = Field(description="Current lap time in seconds")
    last_lap_time: float = Field(description="Last lap time in seconds")
    best_lap_time: float = Field(description="Best lap time in seconds")

    # Vehicle State
    speed: float = Field(description="Speed in meters per second")
    rpm: float = Field(description="Engine RPM")
    gear: int = Field(description="Current gear")

    # Driver Inputs
    throttle: float = Field(description="Throttle position (0-1)")
    brake: float = Field(description="Brake position (0-1)")
    clutch: float = Field(description="Clutch position (0-1)")
    steering_angle: float = Field(description="Steering wheel angle in radians")

    # Vehicle Dynamics
    lateral_acceleration: float = Field(description="Lateral acceleration in m/s²")
    longitudinal_acceleration: float = Field(description="Longitudinal acceleration in m/s²")
    vertical_acceleration: float = Field(description="Vertical acceleration in m/s²")
    yaw_rate: float = Field(description="Yaw rate in rad/s")
    roll_rate: float = Field(description="Roll rate in rad/s")
    pitch_rate: float = Field(description="Pitch rate in rad/s")

    # Vehicle Velocity
    velocity_x: float = Field(description="X velocity in m/s")
    velocity_y: float = Field(description="Y velocity in m/s")
    velocity_z: float = Field(description="Z velocity in m/s")

    # Vehicle Orientation
    yaw: float = Field(description="Yaw orientation in radians")
    pitch: float = Field(description="Pitch orientation in radians")
    roll: float = Field(description="Roll orientation in radians")

    # GPS Position
    latitude: float = Field(description="Latitude in degrees")
    longitude: float = Field(description="Longitude in degrees")
    altitude: float = Field(description="Altitude in meters")

    # Tire Data
    tire_temps: dict[str, dict[str, float]] = Field(
        description="Tire temperatures (LF,RF,LR,RR: left,middle,right)"
    )
    tire_wear: dict[str, dict[str, float]] = Field(
        description="Tire wear percentage (LF,RF,LR,RR: left,middle,right)"
    )
    brake_line_pressure: dict[str, float] = Field(
        description="Brake line pressure per wheel in bar"
    )

    # Track Conditions
    track_temp: float = Field(description="Track temperature in Celsius")
    track_wetness: int = Field(description="Track wetness level")
    air_temp: float = Field(description="Air temperature in Celsius")

    # Session State
    session_flags: int = Field(description="Current session flags")
    track_surface: int = Field(description="Current track surface type")
    on_pit_road: bool = Field(description="Whether car is on pit road")

    @classmethod
    def from_irsdk(cls, source: TelemetryDataSource, timestamp: datetime) -> Self:
        """
        Create a TelemetryFrame from a telemetry data source.

        This method can work with any source that provides telemetry data via
        dictionary-style access, including live iRacing SDK connections and
        recorded IBT file readers.

        Args:
            source: The telemetry data source (live or replay).
            timestamp: The timestamp of the telemetry frame.

        Returns:
            TelemetryFrame: The created TelemetryFrame object.

        Raises:
            KeyError: If required telemetry variables are missing.
        """

        return cls(
            timestamp=timestamp,
            session_time=source["SessionTime"],  # type: ignore
            lap_number=source["Lap"],  # type: ignore
            lap_distance_pct=source["LapDistPct"],  # type: ignore
            lap_distance=source["LapDist"],  # type: ignore
            current_lap_time=source["LapCurrentLapTime"],  # type: ignore
            last_lap_time=source["LapLastLapTime"],  # type: ignore
            best_lap_time=source["LapBestLapTime"],  # type: ignore
            speed=source["Speed"],  # type: ignore
            rpm=source["RPM"],  # type: ignore
            gear=source["Gear"],  # type: ignore
            throttle=source["Throttle"],  # type: ignore
            brake=source["Brake"],  # type: ignore
            clutch=source["Clutch"],  # type: ignore
            steering_angle=source["SteeringWheelAngle"],  # type: ignore
            lateral_acceleration=source["LatAccel"],  # type: ignore
            longitudinal_acceleration=source["LongAccel"],  # type: ignore
            vertical_acceleration=source["VertAccel"],  # type: ignore
            yaw_rate=source["YawRate"],  # type: ignore
            roll_rate=source["RollRate"],  # type: ignore
            pitch_rate=source["PitchRate"],  # type: ignore
            velocity_x=source["VelocityX"],  # type: ignore
            velocity_y=source["VelocityY"],  # type: ignore
            velocity_z=source["VelocityZ"],  # type: ignore
            yaw=source["Yaw"],  # type: ignore
            pitch=source["Pitch"],  # type: ignore
            roll=source["Roll"],  # type: ignore
            latitude=source["Lat"],  # type: ignore
            longitude=source["Lon"],  # type: ignore
            altitude=source["Alt"],  # type: ignore
            tire_temps={
                "LF": {
                    "left": source["LFtempCL"],
                    "middle": source["LFtempCM"],
                    "right": source["LFtempCR"],
                },
                "RF": {
                    "left": source["RFtempCL"],
                    "middle": source["RFtempCM"],
                    "right": source["RFtempCR"],
                },
                "LR": {
                    "left": source["LRtempCL"],
                    "middle": source["LRtempCM"],
                    "right": source["LRtempCR"],
                },
                "RR": {
                    "left": source["RRtempCL"],
                    "middle": source["RRtempCM"],
                    "right": source["RRtempCR"],
                },
            },  # type: ignore
            tire_wear={
                "LF": {
                    "left": source["LFwearL"],
                    "middle": source["LFwearM"],
                    "right": source["LFwearR"],
                },
                "RF": {
                    "left": source["RFwearL"],
                    "middle": source["RFwearM"],
                    "right": source["RFwearR"],
                },
                "LR": {
                    "left": source["LRwearL"],
                    "middle": source["LRwearM"],
                    "right": source["LRwearR"],
                },
                "RR": {
                    "left": source["RRwearL"],
                    "middle": source["RRwearM"],
                    "right": source["RRwearR"],
                },
            },  # type: ignore
            brake_line_pressure={
                "LF": source["LFbrakeLinePress"],
                "RF": source["RFbrakeLinePress"],
                "LR": source["LRbrakeLinePress"],
                "RR": source["RRbrakeLinePress"],
            },  # type: ignore
            track_temp=source["TrackTempCrew"],  # type: ignore
            track_wetness=source["TrackWetness"],  # type: ignore
            air_temp=source["AirTemp"],  # type: ignore
            session_flags=source["SessionFlags"],  # type: ignore
            track_surface=source["PlayerTrackSurface"],  # type: ignore
            on_pit_road=source["OnPitRoad"],  # type: ignore
        )


class SessionFrame(BaseModel):
    """Frame of data pertaining to a session."""

    timestamp: datetime = Field(
        description="Timestamp of the session frame",
        default_factory=lambda: datetime.now(),
    )

    session_id: UUID = Field(description="Session ID", default_factory=uuid4)

    # Track
    track_id: int = Field(description="Track ID")
    track_name: str = Field(description="Track name")
    track_config_name: str = Field(description="Track config name")
    track_type: str = Field(description="Track type", default="road course")

    # Car
    car_id: int = Field(description="Car ID")
    car_name: str = Field(description="Car name")
    car_class_id: int = Field(description="Car class ID")

    # Series
    series_id: int = Field(description="Series ID")

    # Session
    session_type: str = Field(description="Session type")

    @classmethod
    def from_irsdk(cls, source: TelemetryDataSource, timestamp: datetime) -> "SessionFrame":
        """
        Create a SessionFrame from a telemetry data source.

        This method extracts session metadata (track, car, series info) from
        the telemetry source.

        Args:
            source: The telemetry data source (live or replay).
            timestamp: The timestamp of the session frame.

        Returns:
            SessionFrame: The created SessionFrame object.

        Raises:
            KeyError: If required session variables are missing.
        """
        weekend_info = source["WeekendInfo"]
        driver_info = source["DriverInfo"]
        session_info: dict[str, Any] = source["SessionInfo"]  # type: ignore

        session = session_info["Sessions"][session_info["CurrentSessionNum"]]

        car_idx = driver_info["DriverCarIdx"]  # type: ignore

        driver = driver_info["Drivers"][car_idx]  # type: ignore

        return cls(
            timestamp=timestamp,
            track_id=weekend_info["TrackID"],  # type: ignore
            track_name=weekend_info["TrackDisplayName"],  # type: ignore
            track_config_name=weekend_info["TrackConfigName"],  # type: ignore
            track_type=weekend_info["TrackType"],  # type: ignore
            car_id=driver["CarID"],  # type: ignore
            car_name=driver["CarScreenName"],  # type: ignore
            car_class_id=driver["CarClassID"],  # type: ignore
            series_id=weekend_info["SeriesID"],  # type: ignore
            session_type=session["SessionType"],  # type: ignore
        )


class TelemetrySequence(BaseModel):
    frames: list[TelemetryFrame]


class LapTelemetry(TelemetrySequence):
    # frames: list[TelemetryFrame] = Field(
    #     description="List of telemetry frames for the lap"
    # )
    lap_time: float | None = Field(description="Total lap time in seconds")

    @field_validator("frames", mode="before")
    @classmethod
    def validate_frames_not_empty(cls, v: list[Any]) -> list[Any]:
        """Validate that frames list is not empty."""
        if not v:
            raise ValueError("LapTelemetry must contain at least one frame")
        return v

    def to_parquet(self, file_path: str | Path) -> None:
        """Save the LapTelemetry object to a Parquet file."""
        df = pd.DataFrame([frame.model_dump() for frame in self.frames])

        df["lap_time"] = self.lap_time  # will add the value to all rows

        df.to_parquet(file_path)

    @classmethod
    def from_parquet(cls, file_path: str | Path):
        """Load a LapTelemetry object from a Parquet file."""
        df = pd.read_parquet(file_path)

        # lap_time = df["lap_time"].iloc[0]

        # df = df.drop(columns=["lap_time"])

        frames = [TelemetryFrame(**row) for _, row in df.iterrows()]  # type: ignore

        return cls(frames=frames, lap_time=None)

    def get_lap_time(self):
        return self.frames[-1].session_time - self.frames[0].session_time

    def is_valid(self) -> tuple[bool, int]:
        """Check for any off-track or other abnormalities that invalidate the lap."""

        # Can check for current track surface and see if it is off-track
        # Can also check if the incident count has increased since the start of the lap

        for i, frame in enumerate(self.frames):
            # -1: not in world
            # 0: off track
            # 1: pit stall
            # 2: approaching pits
            # 3: on track

            if frame.track_surface != 3:
                return False, i

        return True, -1
