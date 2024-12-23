from pydantic import BaseModel, Field
from datetime import datetime


class TelemetryFrame(BaseModel):
    # Time
    timestamp: datetime = Field(description="Timestamp of the telemetry frame")
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
    longitudinal_acceleration: float = Field(
        description="Longitudinal acceleration in m/s²"
    )
    vertical_acceleration: float = Field(description="Vertical acceleration in m/s²")
    yaw_rate: float = Field(description="Yaw rate in rad/s")
    roll_rate: float = Field(description="Roll rate in rad/s")
    pitch_rate: float = Field(description="Pitch rate in rad/s")

    # Vehicle Position/Orientation
    position_x: float = Field(description="X velocity in m/s")
    position_y: float = Field(description="Y velocity in m/s")
    position_z: float = Field(description="Z velocity in m/s")
    yaw: float = Field(description="Yaw orientation in radians")
    pitch: float = Field(description="Pitch orientation in radians")
    roll: float = Field(description="Roll orientation in radians")

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
    def from_irsdk(cls, ir, timestamp):
        """
        Create a TelemetryFrame object from an iRacing SDK telemetry sample.

        Args:
            ir (dict): The telemetry sample from the iRacing SDK.
            timestamp (datetime.datetime): The timestamp of the telemetry frame.

        Returns:
            TelemetryFrame: The created TelemetryFrame object.
        """
        return cls(
            timestamp=timestamp,
            session_time=ir["SessionTime"],
            lap_number=ir["Lap"],
            lap_distance_pct=ir["LapDistPct"],
            lap_distance=ir["LapDist"],
            current_lap_time=ir["LapCurrentLapTime"],
            last_lap_time=ir["LapLastLapTime"],
            best_lap_time=ir["LapBestLapTime"],
            speed=ir["Speed"],
            rpm=ir["RPM"],
            gear=ir["Gear"],
            throttle=ir["Throttle"],
            brake=ir["Brake"],
            clutch=ir["Clutch"],
            steering_angle=ir["SteeringWheelAngle"],
            lateral_acceleration=ir["LatAccel"],
            longitudinal_acceleration=ir["LongAccel"],
            vertical_acceleration=ir["VertAccel"],
            yaw_rate=ir["YawRate"],
            roll_rate=ir["RollRate"],
            pitch_rate=ir["PitchRate"],
            position_x=ir["VelocityX"],
            position_y=ir["VelocityY"],
            position_z=ir["VelocityZ"],
            yaw=ir["Yaw"],
            pitch=ir["Pitch"],
            roll=ir["Roll"],
            tire_temps={
                "LF": {
                    "left": ir["LFtempCL"],
                    "middle": ir["LFtempCM"],
                    "right": ir["LFtempCR"],
                },
                "RF": {
                    "left": ir["RFtempCL"],
                    "middle": ir["RFtempCM"],
                    "right": ir["RFtempCR"],
                },
                "LR": {
                    "left": ir["LRtempCL"],
                    "middle": ir["LRtempCM"],
                    "right": ir["LRtempCR"],
                },
                "RR": {
                    "left": ir["RRtempCL"],
                    "middle": ir["RRtempCM"],
                    "right": ir["RRtempCR"],
                },
            },
            tire_wear={
                "LF": {
                    "left": ir["LFwearL"],
                    "middle": ir["LFwearM"],
                    "right": ir["LFwearR"],
                },
                "RF": {
                    "left": ir["RFwearL"],
                    "middle": ir["RFwearM"],
                    "right": ir["RFwearR"],
                },
                "LR": {
                    "left": ir["LRwearL"],
                    "middle": ir["LRwearM"],
                    "right": ir["LRwearR"],
                },
                "RR": {
                    "left": ir["RRwearL"],
                    "middle": ir["RRwearM"],
                    "right": ir["RRwearR"],
                },
            },
            brake_line_pressure={
                "LF": ir["LFbrakeLinePress"],
                "RF": ir["RFbrakeLinePress"],
                "LR": ir["LRbrakeLinePress"],
                "RR": ir["RRbrakeLinePress"],
            },
            track_temp=ir["TrackTempCrew"],
            track_wetness=ir["TrackWetness"],
            air_temp=ir["AirTemp"],
            session_flags=ir["SessionFlags"],
            track_surface=ir["PlayerTrackSurface"],
            on_pit_road=ir["OnPitRoad"],
        )