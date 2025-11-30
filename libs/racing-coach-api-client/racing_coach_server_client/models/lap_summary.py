from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="LapSummary")


@_attrs_define
class LapSummary:
    """Summary of a lap for listing purposes.

    Attributes:
        lap_id (str): UUID of the lap
        lap_number (int): Lap number in the session
        lap_time (float | None): Lap time in seconds
        is_valid (bool): Whether the lap is valid
        has_metrics (bool): Whether metrics have been computed for this lap
        created_at (datetime.datetime): When the lap was recorded
    """

    lap_id: str
    lap_number: int
    lap_time: float | None
    is_valid: bool
    has_metrics: bool
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        lap_id = self.lap_id

        lap_number = self.lap_number

        lap_time: float | None
        lap_time = self.lap_time

        is_valid = self.is_valid

        has_metrics = self.has_metrics

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "lap_id": lap_id,
                "lap_number": lap_number,
                "lap_time": lap_time,
                "is_valid": is_valid,
                "has_metrics": has_metrics,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        lap_id = d.pop("lap_id")

        lap_number = d.pop("lap_number")

        def _parse_lap_time(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        lap_time = _parse_lap_time(d.pop("lap_time"))

        is_valid = d.pop("is_valid")

        has_metrics = d.pop("has_metrics")

        created_at = isoparse(d.pop("created_at"))

        lap_summary = cls(
            lap_id=lap_id,
            lap_number=lap_number,
            lap_time=lap_time,
            is_valid=is_valid,
            has_metrics=has_metrics,
            created_at=created_at,
        )

        lap_summary.additional_properties = d
        return lap_summary

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
