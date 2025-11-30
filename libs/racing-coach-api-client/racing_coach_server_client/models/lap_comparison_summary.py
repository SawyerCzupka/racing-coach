from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="LapComparisonSummary")


@_attrs_define
class LapComparisonSummary:
    """Summary statistics for lap comparison.

    Attributes:
        baseline_lap_id (str):
        comparison_lap_id (str):
        baseline_lap_time (float | None):
        comparison_lap_time (float | None):
        lap_time_delta (float | None):
        max_speed_delta (float | None):
        min_speed_delta (float | None):
        average_corner_speed_delta (float | None):
        total_braking_zones_baseline (int):
        total_braking_zones_comparison (int):
        total_corners_baseline (int):
        total_corners_comparison (int):
        matched_braking_zones (int):
        matched_corners (int):
    """

    baseline_lap_id: str
    comparison_lap_id: str
    baseline_lap_time: float | None
    comparison_lap_time: float | None
    lap_time_delta: float | None
    max_speed_delta: float | None
    min_speed_delta: float | None
    average_corner_speed_delta: float | None
    total_braking_zones_baseline: int
    total_braking_zones_comparison: int
    total_corners_baseline: int
    total_corners_comparison: int
    matched_braking_zones: int
    matched_corners: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        baseline_lap_id = self.baseline_lap_id

        comparison_lap_id = self.comparison_lap_id

        baseline_lap_time: float | None
        baseline_lap_time = self.baseline_lap_time

        comparison_lap_time: float | None
        comparison_lap_time = self.comparison_lap_time

        lap_time_delta: float | None
        lap_time_delta = self.lap_time_delta

        max_speed_delta: float | None
        max_speed_delta = self.max_speed_delta

        min_speed_delta: float | None
        min_speed_delta = self.min_speed_delta

        average_corner_speed_delta: float | None
        average_corner_speed_delta = self.average_corner_speed_delta

        total_braking_zones_baseline = self.total_braking_zones_baseline

        total_braking_zones_comparison = self.total_braking_zones_comparison

        total_corners_baseline = self.total_corners_baseline

        total_corners_comparison = self.total_corners_comparison

        matched_braking_zones = self.matched_braking_zones

        matched_corners = self.matched_corners

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "baseline_lap_id": baseline_lap_id,
                "comparison_lap_id": comparison_lap_id,
                "baseline_lap_time": baseline_lap_time,
                "comparison_lap_time": comparison_lap_time,
                "lap_time_delta": lap_time_delta,
                "max_speed_delta": max_speed_delta,
                "min_speed_delta": min_speed_delta,
                "average_corner_speed_delta": average_corner_speed_delta,
                "total_braking_zones_baseline": total_braking_zones_baseline,
                "total_braking_zones_comparison": total_braking_zones_comparison,
                "total_corners_baseline": total_corners_baseline,
                "total_corners_comparison": total_corners_comparison,
                "matched_braking_zones": matched_braking_zones,
                "matched_corners": matched_corners,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        baseline_lap_id = d.pop("baseline_lap_id")

        comparison_lap_id = d.pop("comparison_lap_id")

        def _parse_baseline_lap_time(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        baseline_lap_time = _parse_baseline_lap_time(d.pop("baseline_lap_time"))

        def _parse_comparison_lap_time(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        comparison_lap_time = _parse_comparison_lap_time(d.pop("comparison_lap_time"))

        def _parse_lap_time_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        lap_time_delta = _parse_lap_time_delta(d.pop("lap_time_delta"))

        def _parse_max_speed_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        max_speed_delta = _parse_max_speed_delta(d.pop("max_speed_delta"))

        def _parse_min_speed_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        min_speed_delta = _parse_min_speed_delta(d.pop("min_speed_delta"))

        def _parse_average_corner_speed_delta(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        average_corner_speed_delta = _parse_average_corner_speed_delta(d.pop("average_corner_speed_delta"))

        total_braking_zones_baseline = d.pop("total_braking_zones_baseline")

        total_braking_zones_comparison = d.pop("total_braking_zones_comparison")

        total_corners_baseline = d.pop("total_corners_baseline")

        total_corners_comparison = d.pop("total_corners_comparison")

        matched_braking_zones = d.pop("matched_braking_zones")

        matched_corners = d.pop("matched_corners")

        lap_comparison_summary = cls(
            baseline_lap_id=baseline_lap_id,
            comparison_lap_id=comparison_lap_id,
            baseline_lap_time=baseline_lap_time,
            comparison_lap_time=comparison_lap_time,
            lap_time_delta=lap_time_delta,
            max_speed_delta=max_speed_delta,
            min_speed_delta=min_speed_delta,
            average_corner_speed_delta=average_corner_speed_delta,
            total_braking_zones_baseline=total_braking_zones_baseline,
            total_braking_zones_comparison=total_braking_zones_comparison,
            total_corners_baseline=total_corners_baseline,
            total_corners_comparison=total_corners_comparison,
            matched_braking_zones=matched_braking_zones,
            matched_corners=matched_corners,
        )

        lap_comparison_summary.additional_properties = d
        return lap_comparison_summary

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
