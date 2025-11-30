from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.telemetry_frame_brake_line_pressure import TelemetryFrameBrakeLinePressure
    from ..models.telemetry_frame_tire_temps import TelemetryFrameTireTemps
    from ..models.telemetry_frame_tire_wear import TelemetryFrameTireWear


T = TypeVar("T", bound="TelemetryFrame")


@_attrs_define
class TelemetryFrame:
    """A single frame of driving telemetry data.

    Attributes:
        session_time (float): Seconds since session start
        lap_number (int): Current lap number
        lap_distance_pct (float): Percentage of the lap completed
        lap_distance (float): Meters traveled from S/F this lap
        current_lap_time (float): Current lap time in seconds
        last_lap_time (float): Last lap time in seconds
        best_lap_time (float): Best lap time in seconds
        speed (float): Speed in meters per second
        rpm (float): Engine RPM
        gear (int): Current gear
        throttle (float): Throttle position (0-1)
        brake (float): Brake position (0-1)
        clutch (float): Clutch position (0-1)
        steering_angle (float): Steering wheel angle in radians
        lateral_acceleration (float): Lateral acceleration in m/s²
        longitudinal_acceleration (float): Longitudinal acceleration in m/s²
        vertical_acceleration (float): Vertical acceleration in m/s²
        yaw_rate (float): Yaw rate in rad/s
        roll_rate (float): Roll rate in rad/s
        pitch_rate (float): Pitch rate in rad/s
        velocity_x (float): X velocity in m/s
        velocity_y (float): Y velocity in m/s
        velocity_z (float): Z velocity in m/s
        yaw (float): Yaw orientation in radians
        pitch (float): Pitch orientation in radians
        roll (float): Roll orientation in radians
        latitude (float): Latitude in degrees
        longitude (float): Longitude in degrees
        altitude (float): Altitude in meters
        tire_temps (TelemetryFrameTireTemps): Tire temperatures (LF,RF,LR,RR: left,middle,right)
        tire_wear (TelemetryFrameTireWear): Tire wear percentage (LF,RF,LR,RR: left,middle,right)
        brake_line_pressure (TelemetryFrameBrakeLinePressure): Brake line pressure per wheel in bar
        track_temp (float): Track temperature in Celsius
        track_wetness (int): Track wetness level
        air_temp (float): Air temperature in Celsius
        session_flags (int): Current session flags
        track_surface (int): Current track surface type
        on_pit_road (bool): Whether car is on pit road
        timestamp (datetime.datetime | Unset): Timestamp of the telemetry frame
    """

    session_time: float
    lap_number: int
    lap_distance_pct: float
    lap_distance: float
    current_lap_time: float
    last_lap_time: float
    best_lap_time: float
    speed: float
    rpm: float
    gear: int
    throttle: float
    brake: float
    clutch: float
    steering_angle: float
    lateral_acceleration: float
    longitudinal_acceleration: float
    vertical_acceleration: float
    yaw_rate: float
    roll_rate: float
    pitch_rate: float
    velocity_x: float
    velocity_y: float
    velocity_z: float
    yaw: float
    pitch: float
    roll: float
    latitude: float
    longitude: float
    altitude: float
    tire_temps: TelemetryFrameTireTemps
    tire_wear: TelemetryFrameTireWear
    brake_line_pressure: TelemetryFrameBrakeLinePressure
    track_temp: float
    track_wetness: int
    air_temp: float
    session_flags: int
    track_surface: int
    on_pit_road: bool
    timestamp: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        session_time = self.session_time

        lap_number = self.lap_number

        lap_distance_pct = self.lap_distance_pct

        lap_distance = self.lap_distance

        current_lap_time = self.current_lap_time

        last_lap_time = self.last_lap_time

        best_lap_time = self.best_lap_time

        speed = self.speed

        rpm = self.rpm

        gear = self.gear

        throttle = self.throttle

        brake = self.brake

        clutch = self.clutch

        steering_angle = self.steering_angle

        lateral_acceleration = self.lateral_acceleration

        longitudinal_acceleration = self.longitudinal_acceleration

        vertical_acceleration = self.vertical_acceleration

        yaw_rate = self.yaw_rate

        roll_rate = self.roll_rate

        pitch_rate = self.pitch_rate

        velocity_x = self.velocity_x

        velocity_y = self.velocity_y

        velocity_z = self.velocity_z

        yaw = self.yaw

        pitch = self.pitch

        roll = self.roll

        latitude = self.latitude

        longitude = self.longitude

        altitude = self.altitude

        tire_temps = self.tire_temps.to_dict()

        tire_wear = self.tire_wear.to_dict()

        brake_line_pressure = self.brake_line_pressure.to_dict()

        track_temp = self.track_temp

        track_wetness = self.track_wetness

        air_temp = self.air_temp

        session_flags = self.session_flags

        track_surface = self.track_surface

        on_pit_road = self.on_pit_road

        timestamp: str | Unset = UNSET
        if not isinstance(self.timestamp, Unset):
            timestamp = self.timestamp.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "session_time": session_time,
                "lap_number": lap_number,
                "lap_distance_pct": lap_distance_pct,
                "lap_distance": lap_distance,
                "current_lap_time": current_lap_time,
                "last_lap_time": last_lap_time,
                "best_lap_time": best_lap_time,
                "speed": speed,
                "rpm": rpm,
                "gear": gear,
                "throttle": throttle,
                "brake": brake,
                "clutch": clutch,
                "steering_angle": steering_angle,
                "lateral_acceleration": lateral_acceleration,
                "longitudinal_acceleration": longitudinal_acceleration,
                "vertical_acceleration": vertical_acceleration,
                "yaw_rate": yaw_rate,
                "roll_rate": roll_rate,
                "pitch_rate": pitch_rate,
                "velocity_x": velocity_x,
                "velocity_y": velocity_y,
                "velocity_z": velocity_z,
                "yaw": yaw,
                "pitch": pitch,
                "roll": roll,
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "tire_temps": tire_temps,
                "tire_wear": tire_wear,
                "brake_line_pressure": brake_line_pressure,
                "track_temp": track_temp,
                "track_wetness": track_wetness,
                "air_temp": air_temp,
                "session_flags": session_flags,
                "track_surface": track_surface,
                "on_pit_road": on_pit_road,
            }
        )
        if timestamp is not UNSET:
            field_dict["timestamp"] = timestamp

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.telemetry_frame_brake_line_pressure import TelemetryFrameBrakeLinePressure
        from ..models.telemetry_frame_tire_temps import TelemetryFrameTireTemps
        from ..models.telemetry_frame_tire_wear import TelemetryFrameTireWear

        d = dict(src_dict)
        session_time = d.pop("session_time")

        lap_number = d.pop("lap_number")

        lap_distance_pct = d.pop("lap_distance_pct")

        lap_distance = d.pop("lap_distance")

        current_lap_time = d.pop("current_lap_time")

        last_lap_time = d.pop("last_lap_time")

        best_lap_time = d.pop("best_lap_time")

        speed = d.pop("speed")

        rpm = d.pop("rpm")

        gear = d.pop("gear")

        throttle = d.pop("throttle")

        brake = d.pop("brake")

        clutch = d.pop("clutch")

        steering_angle = d.pop("steering_angle")

        lateral_acceleration = d.pop("lateral_acceleration")

        longitudinal_acceleration = d.pop("longitudinal_acceleration")

        vertical_acceleration = d.pop("vertical_acceleration")

        yaw_rate = d.pop("yaw_rate")

        roll_rate = d.pop("roll_rate")

        pitch_rate = d.pop("pitch_rate")

        velocity_x = d.pop("velocity_x")

        velocity_y = d.pop("velocity_y")

        velocity_z = d.pop("velocity_z")

        yaw = d.pop("yaw")

        pitch = d.pop("pitch")

        roll = d.pop("roll")

        latitude = d.pop("latitude")

        longitude = d.pop("longitude")

        altitude = d.pop("altitude")

        tire_temps = TelemetryFrameTireTemps.from_dict(d.pop("tire_temps"))

        tire_wear = TelemetryFrameTireWear.from_dict(d.pop("tire_wear"))

        brake_line_pressure = TelemetryFrameBrakeLinePressure.from_dict(d.pop("brake_line_pressure"))

        track_temp = d.pop("track_temp")

        track_wetness = d.pop("track_wetness")

        air_temp = d.pop("air_temp")

        session_flags = d.pop("session_flags")

        track_surface = d.pop("track_surface")

        on_pit_road = d.pop("on_pit_road")

        _timestamp = d.pop("timestamp", UNSET)
        timestamp: datetime.datetime | Unset
        if isinstance(_timestamp, Unset):
            timestamp = UNSET
        else:
            timestamp = isoparse(_timestamp)

        telemetry_frame = cls(
            session_time=session_time,
            lap_number=lap_number,
            lap_distance_pct=lap_distance_pct,
            lap_distance=lap_distance,
            current_lap_time=current_lap_time,
            last_lap_time=last_lap_time,
            best_lap_time=best_lap_time,
            speed=speed,
            rpm=rpm,
            gear=gear,
            throttle=throttle,
            brake=brake,
            clutch=clutch,
            steering_angle=steering_angle,
            lateral_acceleration=lateral_acceleration,
            longitudinal_acceleration=longitudinal_acceleration,
            vertical_acceleration=vertical_acceleration,
            yaw_rate=yaw_rate,
            roll_rate=roll_rate,
            pitch_rate=pitch_rate,
            velocity_x=velocity_x,
            velocity_y=velocity_y,
            velocity_z=velocity_z,
            yaw=yaw,
            pitch=pitch,
            roll=roll,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            tire_temps=tire_temps,
            tire_wear=tire_wear,
            brake_line_pressure=brake_line_pressure,
            track_temp=track_temp,
            track_wetness=track_wetness,
            air_temp=air_temp,
            session_flags=session_flags,
            track_surface=track_surface,
            on_pit_road=on_pit_road,
            timestamp=timestamp,
        )

        telemetry_frame.additional_properties = d
        return telemetry_frame

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
