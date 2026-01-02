from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.corner_segment_response import CornerSegmentResponse


T = TypeVar("T", bound="CornerSegmentListResponse")


@_attrs_define
class CornerSegmentListResponse:
    """Response for listing corner segments.

    Attributes:
        corners (list[CornerSegmentResponse]): List of corner segments
        total (int): Total number of corner segments
    """

    corners: list[CornerSegmentResponse]
    total: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        corners = []
        for corners_item_data in self.corners:
            corners_item = corners_item_data.to_dict()
            corners.append(corners_item)

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "corners": corners,
                "total": total,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.corner_segment_response import CornerSegmentResponse

        d = dict(src_dict)
        corners = []
        _corners = d.pop("corners")
        for corners_item_data in _corners:
            corners_item = CornerSegmentResponse.from_dict(corners_item_data)

            corners.append(corners_item)

        total = d.pop("total")

        corner_segment_list_response = cls(
            corners=corners,
            total=total,
        )

        corner_segment_list_response.additional_properties = d
        return corner_segment_list_response

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
