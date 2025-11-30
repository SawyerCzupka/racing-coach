from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="BrakingMetrics")


@_attrs_define
class BrakingMetrics:
    """
    Attributes:
        braking_point_distance (float):
        braking_point_speed (float):
        end_distance (float):
        max_brake_pressure (float):
        braking_duration (float):
        minimum_speed (float):
        initial_deceleration (float):
        average_deceleration (float):
        braking_efficiency (float):
        has_trail_braking (bool):
        trail_brake_distance (float):
        trail_brake_percentage (float):
    """

    braking_point_distance: float
    braking_point_speed: float
    end_distance: float
    max_brake_pressure: float
    braking_duration: float
    minimum_speed: float
    initial_deceleration: float
    average_deceleration: float
    braking_efficiency: float
    has_trail_braking: bool
    trail_brake_distance: float
    trail_brake_percentage: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        braking_point_distance = self.braking_point_distance

        braking_point_speed = self.braking_point_speed

        end_distance = self.end_distance

        max_brake_pressure = self.max_brake_pressure

        braking_duration = self.braking_duration

        minimum_speed = self.minimum_speed

        initial_deceleration = self.initial_deceleration

        average_deceleration = self.average_deceleration

        braking_efficiency = self.braking_efficiency

        has_trail_braking = self.has_trail_braking

        trail_brake_distance = self.trail_brake_distance

        trail_brake_percentage = self.trail_brake_percentage

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "braking_point_distance": braking_point_distance,
                "braking_point_speed": braking_point_speed,
                "end_distance": end_distance,
                "max_brake_pressure": max_brake_pressure,
                "braking_duration": braking_duration,
                "minimum_speed": minimum_speed,
                "initial_deceleration": initial_deceleration,
                "average_deceleration": average_deceleration,
                "braking_efficiency": braking_efficiency,
                "has_trail_braking": has_trail_braking,
                "trail_brake_distance": trail_brake_distance,
                "trail_brake_percentage": trail_brake_percentage,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        braking_point_distance = d.pop("braking_point_distance")

        braking_point_speed = d.pop("braking_point_speed")

        end_distance = d.pop("end_distance")

        max_brake_pressure = d.pop("max_brake_pressure")

        braking_duration = d.pop("braking_duration")

        minimum_speed = d.pop("minimum_speed")

        initial_deceleration = d.pop("initial_deceleration")

        average_deceleration = d.pop("average_deceleration")

        braking_efficiency = d.pop("braking_efficiency")

        has_trail_braking = d.pop("has_trail_braking")

        trail_brake_distance = d.pop("trail_brake_distance")

        trail_brake_percentage = d.pop("trail_brake_percentage")

        braking_metrics = cls(
            braking_point_distance=braking_point_distance,
            braking_point_speed=braking_point_speed,
            end_distance=end_distance,
            max_brake_pressure=max_brake_pressure,
            braking_duration=braking_duration,
            minimum_speed=minimum_speed,
            initial_deceleration=initial_deceleration,
            average_deceleration=average_deceleration,
            braking_efficiency=braking_efficiency,
            has_trail_braking=has_trail_braking,
            trail_brake_distance=trail_brake_distance,
            trail_brake_percentage=trail_brake_percentage,
        )

        braking_metrics.additional_properties = d
        return braking_metrics

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
