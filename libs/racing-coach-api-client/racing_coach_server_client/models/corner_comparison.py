from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CornerComparison")


@_attrs_define
class CornerComparison:
    """Comparison data for a corner between two laps.

    Attributes:
        corner_index (int):
        matched_corner_index (int | None):
        baseline_apex_distance (float):
        comparison_apex_distance (float | None):
        distance_delta (float | None):
        turn_in_speed_delta (float | None):
        apex_speed_delta (float | None):
        exit_speed_delta (float | None):
        max_lateral_g_delta (float | None):
        time_in_corner_delta (float | None):
        corner_distance_delta (float | None):
    """

    corner_index: int
    matched_corner_index: int | None
    baseline_apex_distance: float
    comparison_apex_distance: float | None
    distance_delta: float | None
    turn_in_speed_delta: float | None
    apex_speed_delta: float | None
    exit_speed_delta: float | None
    max_lateral_g_delta: float | None
    time_in_corner_delta: float | None
    corner_distance_delta: float | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        corner_index = self.corner_index

        matched_corner_index: int | None
        matched_corner_index = self.matched_corner_index

        baseline_apex_distance = self.baseline_apex_distance

        comparison_apex_distance: float | None
        comparison_apex_distance = self.comparison_apex_distance

        distance_delta: float | None
        distance_delta = self.distance_delta

        turn_in_speed_delta: float | None
        turn_in_speed_delta = self.turn_in_speed_delta

        apex_speed_delta: float | None
        apex_speed_delta = self.apex_speed_delta

        exit_speed_delta: float | None
        exit_speed_delta = self.exit_speed_delta

        max_lateral_g_delta: float | None
        max_lateral_g_delta = self.max_lateral_g_delta

        time_in_corner_delta: float | None
        time_in_corner_delta = self.time_in_corner_delta

        corner_distance_delta: float | None
        corner_distance_delta = self.corner_distance_delta

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "corner_index": corner_index,
                "matched_corner_index": matched_corner_index,
                "baseline_apex_distance": baseline_apex_distance,
                "comparison_apex_distance": comparison_apex_distance,
                "distance_delta": distance_delta,
                "turn_in_speed_delta": turn_in_speed_delta,
                "apex_speed_delta": apex_speed_delta,
                "exit_speed_delta": exit_speed_delta,
                "max_lateral_g_delta": max_lateral_g_delta,
                "time_in_corner_delta": time_in_corner_delta,
                "corner_distance_delta": corner_distance_delta,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        corner_index = d.pop("corner_index")

        def _parse_matched_corner_index(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        matched_corner_index = _parse_matched_corner_index(d.pop("matched_corner_index"))

        baseline_apex_distance = d.pop("baseline_apex_distance")

        def _parse_comparison_apex_distance(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        comparison_apex_distance = _parse_comparison_apex_distance(d.pop("comparison_apex_distance"))

        def _parse_distance_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        distance_delta = _parse_distance_delta(d.pop("distance_delta"))

        def _parse_turn_in_speed_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        turn_in_speed_delta = _parse_turn_in_speed_delta(d.pop("turn_in_speed_delta"))

        def _parse_apex_speed_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        apex_speed_delta = _parse_apex_speed_delta(d.pop("apex_speed_delta"))

        def _parse_exit_speed_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        exit_speed_delta = _parse_exit_speed_delta(d.pop("exit_speed_delta"))

        def _parse_max_lateral_g_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        max_lateral_g_delta = _parse_max_lateral_g_delta(d.pop("max_lateral_g_delta"))

        def _parse_time_in_corner_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        time_in_corner_delta = _parse_time_in_corner_delta(d.pop("time_in_corner_delta"))

        def _parse_corner_distance_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        corner_distance_delta = _parse_corner_distance_delta(d.pop("corner_distance_delta"))

        corner_comparison = cls(
            corner_index=corner_index,
            matched_corner_index=matched_corner_index,
            baseline_apex_distance=baseline_apex_distance,
            comparison_apex_distance=comparison_apex_distance,
            distance_delta=distance_delta,
            turn_in_speed_delta=turn_in_speed_delta,
            apex_speed_delta=apex_speed_delta,
            exit_speed_delta=exit_speed_delta,
            max_lateral_g_delta=max_lateral_g_delta,
            time_in_corner_delta=time_in_corner_delta,
            corner_distance_delta=corner_distance_delta,
        )

        corner_comparison.additional_properties = d
        return corner_comparison

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
