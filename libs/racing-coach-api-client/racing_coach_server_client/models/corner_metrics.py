from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CornerMetrics")


@_attrs_define
class CornerMetrics:
    """
    Attributes:
        turn_in_distance (float):
        apex_distance (float):
        exit_distance (float):
        throttle_application_distance (float):
        turn_in_speed (float):
        apex_speed (float):
        exit_speed (float):
        throttle_application_speed (float):
        max_lateral_g (float):
        time_in_corner (float):
        corner_distance (float):
        max_steering_angle (float):
        speed_loss (float):
        speed_gain (float):
    """

    turn_in_distance: float
    apex_distance: float
    exit_distance: float
    throttle_application_distance: float
    turn_in_speed: float
    apex_speed: float
    exit_speed: float
    throttle_application_speed: float
    max_lateral_g: float
    time_in_corner: float
    corner_distance: float
    max_steering_angle: float
    speed_loss: float
    speed_gain: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        turn_in_distance = self.turn_in_distance

        apex_distance = self.apex_distance

        exit_distance = self.exit_distance

        throttle_application_distance = self.throttle_application_distance

        turn_in_speed = self.turn_in_speed

        apex_speed = self.apex_speed

        exit_speed = self.exit_speed

        throttle_application_speed = self.throttle_application_speed

        max_lateral_g = self.max_lateral_g

        time_in_corner = self.time_in_corner

        corner_distance = self.corner_distance

        max_steering_angle = self.max_steering_angle

        speed_loss = self.speed_loss

        speed_gain = self.speed_gain

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "turn_in_distance": turn_in_distance,
                "apex_distance": apex_distance,
                "exit_distance": exit_distance,
                "throttle_application_distance": throttle_application_distance,
                "turn_in_speed": turn_in_speed,
                "apex_speed": apex_speed,
                "exit_speed": exit_speed,
                "throttle_application_speed": throttle_application_speed,
                "max_lateral_g": max_lateral_g,
                "time_in_corner": time_in_corner,
                "corner_distance": corner_distance,
                "max_steering_angle": max_steering_angle,
                "speed_loss": speed_loss,
                "speed_gain": speed_gain,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        turn_in_distance = d.pop("turn_in_distance")

        apex_distance = d.pop("apex_distance")

        exit_distance = d.pop("exit_distance")

        throttle_application_distance = d.pop("throttle_application_distance")

        turn_in_speed = d.pop("turn_in_speed")

        apex_speed = d.pop("apex_speed")

        exit_speed = d.pop("exit_speed")

        throttle_application_speed = d.pop("throttle_application_speed")

        max_lateral_g = d.pop("max_lateral_g")

        time_in_corner = d.pop("time_in_corner")

        corner_distance = d.pop("corner_distance")

        max_steering_angle = d.pop("max_steering_angle")

        speed_loss = d.pop("speed_loss")

        speed_gain = d.pop("speed_gain")

        corner_metrics = cls(
            turn_in_distance=turn_in_distance,
            apex_distance=apex_distance,
            exit_distance=exit_distance,
            throttle_application_distance=throttle_application_distance,
            turn_in_speed=turn_in_speed,
            apex_speed=apex_speed,
            exit_speed=exit_speed,
            throttle_application_speed=throttle_application_speed,
            max_lateral_g=max_lateral_g,
            time_in_corner=time_in_corner,
            corner_distance=corner_distance,
            max_steering_angle=max_steering_angle,
            speed_loss=speed_loss,
            speed_gain=speed_gain,
        )

        corner_metrics.additional_properties = d
        return corner_metrics

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
