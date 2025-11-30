from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="BrakingZoneComparison")


@_attrs_define
class BrakingZoneComparison:
    """Comparison data for a braking zone between two laps.

    Attributes:
        zone_index (int):
        matched_zone_index (int | None):
        baseline_distance (float):
        comparison_distance (float | None):
        distance_delta (float | None):
        braking_point_speed_delta (float | None):
        max_brake_pressure_delta (float | None):
        braking_duration_delta (float | None):
        minimum_speed_delta (float | None):
        braking_efficiency_delta (float | None):
        trail_braking_comparison (None | str):
    """

    zone_index: int
    matched_zone_index: int | None
    baseline_distance: float
    comparison_distance: float | None
    distance_delta: float | None
    braking_point_speed_delta: float | None
    max_brake_pressure_delta: float | None
    braking_duration_delta: float | None
    minimum_speed_delta: float | None
    braking_efficiency_delta: float | None
    trail_braking_comparison: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        zone_index = self.zone_index

        matched_zone_index: int | None
        matched_zone_index = self.matched_zone_index

        baseline_distance = self.baseline_distance

        comparison_distance: float | None
        comparison_distance = self.comparison_distance

        distance_delta: float | None
        distance_delta = self.distance_delta

        braking_point_speed_delta: float | None
        braking_point_speed_delta = self.braking_point_speed_delta

        max_brake_pressure_delta: float | None
        max_brake_pressure_delta = self.max_brake_pressure_delta

        braking_duration_delta: float | None
        braking_duration_delta = self.braking_duration_delta

        minimum_speed_delta: float | None
        minimum_speed_delta = self.minimum_speed_delta

        braking_efficiency_delta: float | None
        braking_efficiency_delta = self.braking_efficiency_delta

        trail_braking_comparison: None | str
        trail_braking_comparison = self.trail_braking_comparison

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "zone_index": zone_index,
                "matched_zone_index": matched_zone_index,
                "baseline_distance": baseline_distance,
                "comparison_distance": comparison_distance,
                "distance_delta": distance_delta,
                "braking_point_speed_delta": braking_point_speed_delta,
                "max_brake_pressure_delta": max_brake_pressure_delta,
                "braking_duration_delta": braking_duration_delta,
                "minimum_speed_delta": minimum_speed_delta,
                "braking_efficiency_delta": braking_efficiency_delta,
                "trail_braking_comparison": trail_braking_comparison,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        zone_index = d.pop("zone_index")

        def _parse_matched_zone_index(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        matched_zone_index = _parse_matched_zone_index(d.pop("matched_zone_index"))

        baseline_distance = d.pop("baseline_distance")

        def _parse_comparison_distance(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        comparison_distance = _parse_comparison_distance(d.pop("comparison_distance"))

        def _parse_distance_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        distance_delta = _parse_distance_delta(d.pop("distance_delta"))

        def _parse_braking_point_speed_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        braking_point_speed_delta = _parse_braking_point_speed_delta(d.pop("braking_point_speed_delta"))

        def _parse_max_brake_pressure_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        max_brake_pressure_delta = _parse_max_brake_pressure_delta(d.pop("max_brake_pressure_delta"))

        def _parse_braking_duration_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        braking_duration_delta = _parse_braking_duration_delta(d.pop("braking_duration_delta"))

        def _parse_minimum_speed_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        minimum_speed_delta = _parse_minimum_speed_delta(d.pop("minimum_speed_delta"))

        def _parse_braking_efficiency_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        braking_efficiency_delta = _parse_braking_efficiency_delta(d.pop("braking_efficiency_delta"))

        def _parse_trail_braking_comparison(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        trail_braking_comparison = _parse_trail_braking_comparison(d.pop("trail_braking_comparison"))

        braking_zone_comparison = cls(
            zone_index=zone_index,
            matched_zone_index=matched_zone_index,
            baseline_distance=baseline_distance,
            comparison_distance=comparison_distance,
            distance_delta=distance_delta,
            braking_point_speed_delta=braking_point_speed_delta,
            max_brake_pressure_delta=max_brake_pressure_delta,
            braking_duration_delta=braking_duration_delta,
            minimum_speed_delta=minimum_speed_delta,
            braking_efficiency_delta=braking_efficiency_delta,
            trail_braking_comparison=trail_braking_comparison,
        )

        braking_zone_comparison.additional_properties = d
        return braking_zone_comparison

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
