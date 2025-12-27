from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.corner_segment_create import CornerSegmentCreate


T = TypeVar("T", bound="CornerSegmentBulkRequest")


@_attrs_define
class CornerSegmentBulkRequest:
    """Request for bulk creating/replacing corner segments.

    Attributes:
        corners (list[CornerSegmentCreate]): List of corner segments in order (corner 1, 2, 3...)
    """

    corners: list[CornerSegmentCreate]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        corners = []
        for corners_item_data in self.corners:
            corners_item = corners_item_data.to_dict()
            corners.append(corners_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "corners": corners,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.corner_segment_create import CornerSegmentCreate

        d = dict(src_dict)
        corners = []
        _corners = d.pop("corners")
        for corners_item_data in _corners:
            corners_item = CornerSegmentCreate.from_dict(corners_item_data)

            corners.append(corners_item)

        corner_segment_bulk_request = cls(
            corners=corners,
        )

        corner_segment_bulk_request.additional_properties = d
        return corner_segment_bulk_request

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
