from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CornerSegmentCreate")


@_attrs_define
class CornerSegmentCreate:
    """Schema for creating a corner segment.

    Attributes:
        start_distance (float): Start distance in meters from S/F line
        end_distance (float): End distance in meters from S/F line
    """

    start_distance: float
    end_distance: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        start_distance = self.start_distance

        end_distance = self.end_distance

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "start_distance": start_distance,
                "end_distance": end_distance,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        start_distance = d.pop("start_distance")

        end_distance = d.pop("end_distance")

        corner_segment_create = cls(
            start_distance=start_distance,
            end_distance=end_distance,
        )

        corner_segment_create.additional_properties = d
        return corner_segment_create

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
