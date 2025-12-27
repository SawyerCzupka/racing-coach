from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.track_boundary_summary import TrackBoundarySummary


T = TypeVar("T", bound="TrackBoundaryListResponse")


@_attrs_define
class TrackBoundaryListResponse:
    """Response model for track boundary list endpoint.

    Attributes:
        boundaries (list[TrackBoundarySummary]): List of track boundaries
        total (int): Total number of track boundaries
    """

    boundaries: list[TrackBoundarySummary]
    total: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        boundaries = []
        for boundaries_item_data in self.boundaries:
            boundaries_item = boundaries_item_data.to_dict()
            boundaries.append(boundaries_item)

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "boundaries": boundaries,
                "total": total,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.track_boundary_summary import TrackBoundarySummary

        d = dict(src_dict)
        boundaries = []
        _boundaries = d.pop("boundaries")
        for boundaries_item_data in _boundaries:
            boundaries_item = TrackBoundarySummary.from_dict(boundaries_item_data)

            boundaries.append(boundaries_item)

        total = d.pop("total")

        track_boundary_list_response = cls(
            boundaries=boundaries,
            total=total,
        )

        track_boundary_list_response.additional_properties = d
        return track_boundary_list_response

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
