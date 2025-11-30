from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.braking_metrics import BrakingMetrics
    from ..models.corner_metrics import CornerMetrics


T = TypeVar("T", bound="LapMetrics")


@_attrs_define
class LapMetrics:
    """
    Attributes:
        lap_number (int):
        lap_time (float | None):
        braking_zones (list[BrakingMetrics]):
        corners (list[CornerMetrics]):
        total_corners (int):
        total_braking_zones (int):
        average_corner_speed (float):
        max_speed (float):
        min_speed (float):
    """

    lap_number: int
    lap_time: float | None
    braking_zones: list[BrakingMetrics]
    corners: list[CornerMetrics]
    total_corners: int
    total_braking_zones: int
    average_corner_speed: float
    max_speed: float
    min_speed: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        lap_number = self.lap_number

        lap_time: float | None
        lap_time = self.lap_time

        braking_zones = []
        for braking_zones_item_data in self.braking_zones:
            braking_zones_item = braking_zones_item_data.to_dict()
            braking_zones.append(braking_zones_item)

        corners = []
        for corners_item_data in self.corners:
            corners_item = corners_item_data.to_dict()
            corners.append(corners_item)

        total_corners = self.total_corners

        total_braking_zones = self.total_braking_zones

        average_corner_speed = self.average_corner_speed

        max_speed = self.max_speed

        min_speed = self.min_speed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "lap_number": lap_number,
                "lap_time": lap_time,
                "braking_zones": braking_zones,
                "corners": corners,
                "total_corners": total_corners,
                "total_braking_zones": total_braking_zones,
                "average_corner_speed": average_corner_speed,
                "max_speed": max_speed,
                "min_speed": min_speed,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.braking_metrics import BrakingMetrics
        from ..models.corner_metrics import CornerMetrics

        d = dict(src_dict)
        lap_number = d.pop("lap_number")

        def _parse_lap_time(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        lap_time = _parse_lap_time(d.pop("lap_time"))

        braking_zones = []
        _braking_zones = d.pop("braking_zones")
        for braking_zones_item_data in _braking_zones:
            braking_zones_item = BrakingMetrics.from_dict(braking_zones_item_data)

            braking_zones.append(braking_zones_item)

        corners = []
        _corners = d.pop("corners")
        for corners_item_data in _corners:
            corners_item = CornerMetrics.from_dict(corners_item_data)

            corners.append(corners_item)

        total_corners = d.pop("total_corners")

        total_braking_zones = d.pop("total_braking_zones")

        average_corner_speed = d.pop("average_corner_speed")

        max_speed = d.pop("max_speed")

        min_speed = d.pop("min_speed")

        lap_metrics = cls(
            lap_number=lap_number,
            lap_time=lap_time,
            braking_zones=braking_zones,
            corners=corners,
            total_corners=total_corners,
            total_braking_zones=total_braking_zones,
            average_corner_speed=average_corner_speed,
            max_speed=max_speed,
            min_speed=min_speed,
        )

        lap_metrics.additional_properties = d
        return lap_metrics

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
