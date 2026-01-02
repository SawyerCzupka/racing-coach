from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="CornerSegmentResponse")


@_attrs_define
class CornerSegmentResponse:
    """Response schema for a corner segment.

    Attributes:
        id (str): UUID of the corner segment
        corner_number (int): Corner number (1-indexed, derived from sort order)
        start_distance (float): Start distance in meters from S/F line
        end_distance (float): End distance in meters from S/F line
        created_at (datetime.datetime): When the corner segment was created
        updated_at (datetime.datetime): When the corner segment was last updated
    """

    id: str
    corner_number: int
    start_distance: float
    end_distance: float
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        corner_number = self.corner_number

        start_distance = self.start_distance

        end_distance = self.end_distance

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "corner_number": corner_number,
                "start_distance": start_distance,
                "end_distance": end_distance,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        corner_number = d.pop("corner_number")

        start_distance = d.pop("start_distance")

        end_distance = d.pop("end_distance")

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        corner_segment_response = cls(
            id=id,
            corner_number=corner_number,
            start_distance=start_distance,
            end_distance=end_distance,
            created_at=created_at,
            updated_at=updated_at,
        )

        corner_segment_response.additional_properties = d
        return corner_segment_response

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
