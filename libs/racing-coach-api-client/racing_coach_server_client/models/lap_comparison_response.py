from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.braking_zone_comparison import BrakingZoneComparison
    from ..models.corner_comparison import CornerComparison
    from ..models.lap_comparison_summary import LapComparisonSummary


T = TypeVar("T", bound="LapComparisonResponse")


@_attrs_define
class LapComparisonResponse:
    """Complete lap comparison response.

    Attributes:
        summary (LapComparisonSummary): Summary statistics for lap comparison.
        braking_zone_comparisons (list[BrakingZoneComparison]):
        corner_comparisons (list[CornerComparison]):
    """

    summary: LapComparisonSummary
    braking_zone_comparisons: list[BrakingZoneComparison]
    corner_comparisons: list[CornerComparison]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        summary = self.summary.to_dict()

        braking_zone_comparisons = []
        for braking_zone_comparisons_item_data in self.braking_zone_comparisons:
            braking_zone_comparisons_item = braking_zone_comparisons_item_data.to_dict()
            braking_zone_comparisons.append(braking_zone_comparisons_item)

        corner_comparisons = []
        for corner_comparisons_item_data in self.corner_comparisons:
            corner_comparisons_item = corner_comparisons_item_data.to_dict()
            corner_comparisons.append(corner_comparisons_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "summary": summary,
                "braking_zone_comparisons": braking_zone_comparisons,
                "corner_comparisons": corner_comparisons,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.braking_zone_comparison import BrakingZoneComparison
        from ..models.corner_comparison import CornerComparison
        from ..models.lap_comparison_summary import LapComparisonSummary

        d = dict(src_dict)
        summary = LapComparisonSummary.from_dict(d.pop("summary"))

        braking_zone_comparisons = []
        _braking_zone_comparisons = d.pop("braking_zone_comparisons")
        for braking_zone_comparisons_item_data in _braking_zone_comparisons:
            braking_zone_comparisons_item = BrakingZoneComparison.from_dict(braking_zone_comparisons_item_data)

            braking_zone_comparisons.append(braking_zone_comparisons_item)

        corner_comparisons = []
        _corner_comparisons = d.pop("corner_comparisons")
        for corner_comparisons_item_data in _corner_comparisons:
            corner_comparisons_item = CornerComparison.from_dict(corner_comparisons_item_data)

            corner_comparisons.append(corner_comparisons_item)

        lap_comparison_response = cls(
            summary=summary,
            braking_zone_comparisons=braking_zone_comparisons,
            corner_comparisons=corner_comparisons,
        )

        lap_comparison_response.additional_properties = d
        return lap_comparison_response

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
