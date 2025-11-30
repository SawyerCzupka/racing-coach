from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="TelemetryFrameResponse")


@_attrs_define
class TelemetryFrameResponse:
    """Response model for a single telemetry frame.

    Attributes:
        timestamp (datetime.datetime):
        session_time (float):
        lap_number (int):
        lap_distance_pct (float):
        lap_distance (float):
        current_lap_time (float):
        speed (float):
        rpm (float):
        gear (int):
        throttle (float):
        brake (float):
        clutch (float):
        steering_angle (float):
        lateral_acceleration (float):
        longitudinal_acceleration (float):
        vertical_acceleration (float):
        yaw_rate (float):
        roll_rate (float):
        pitch_rate (float):
        velocity_x (float):
        velocity_y (float):
        velocity_z (float):
        yaw (float):
        pitch (float):
        roll (float):
        latitude (float):
        longitude (float):
        altitude (float):
        track_temp (float | None | Unset):
        air_temp (float | None | Unset):
    """

    timestamp: datetime.datetime
    session_time: float
    lap_number: int
    lap_distance_pct: float
    lap_distance: float
    current_lap_time: float
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
    track_temp: float | None | Unset = UNSET
    air_temp: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        timestamp = self.timestamp.isoformat()

        session_time = self.session_time

        lap_number = self.lap_number

        lap_distance_pct = self.lap_distance_pct

        lap_distance = self.lap_distance

        current_lap_time = self.current_lap_time

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

        track_temp: float | None | Unset
        if isinstance(self.track_temp, Unset):
            track_temp = UNSET
        else:
            track_temp = self.track_temp

        air_temp: float | None | Unset
        if isinstance(self.air_temp, Unset):
            air_temp = UNSET
        else:
            air_temp = self.air_temp

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "timestamp": timestamp,
                "session_time": session_time,
                "lap_number": lap_number,
                "lap_distance_pct": lap_distance_pct,
                "lap_distance": lap_distance,
                "current_lap_time": current_lap_time,
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
            }
        )
        if track_temp is not UNSET:
            field_dict["track_temp"] = track_temp
        if air_temp is not UNSET:
            field_dict["air_temp"] = air_temp

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        timestamp = isoparse(d.pop("timestamp"))

        session_time = d.pop("session_time")

        lap_number = d.pop("lap_number")

        lap_distance_pct = d.pop("lap_distance_pct")

        lap_distance = d.pop("lap_distance")

        current_lap_time = d.pop("current_lap_time")

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

        def _parse_track_temp(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        track_temp = _parse_track_temp(d.pop("track_temp", UNSET))

        def _parse_air_temp(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        air_temp = _parse_air_temp(d.pop("air_temp", UNSET))

        telemetry_frame_response = cls(
            timestamp=timestamp,
            session_time=session_time,
            lap_number=lap_number,
            lap_distance_pct=lap_distance_pct,
            lap_distance=lap_distance,
            current_lap_time=current_lap_time,
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
            track_temp=track_temp,
            air_temp=air_temp,
        )

        telemetry_frame_response.additional_properties = d
        return telemetry_frame_response

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
