from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="TrackBoundarySummary")


@_attrs_define
class TrackBoundarySummary:
    """Summary of a track boundary for listing purposes.

    Attributes:
        id (str): UUID of the track boundary
        track_id (int): iRacing track ID
        track_name (str): Name of the track
        track_config_name (None | str): Track configuration name
        grid_size (int): Number of grid points in boundary data
        track_length (float | None): Total track length in meters
        created_at (datetime.datetime): When the boundary was created
    """

    id: str
    track_id: int
    track_name: str
    track_config_name: None | str
    grid_size: int
    track_length: float | None
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        track_id = self.track_id

        track_name = self.track_name

        track_config_name: None | str
        track_config_name = self.track_config_name

        grid_size = self.grid_size

        track_length: float | None
        track_length = self.track_length

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "track_id": track_id,
                "track_name": track_name,
                "track_config_name": track_config_name,
                "grid_size": grid_size,
                "track_length": track_length,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        track_id = d.pop("track_id")

        track_name = d.pop("track_name")

        def _parse_track_config_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        track_config_name = _parse_track_config_name(d.pop("track_config_name"))

        grid_size = d.pop("grid_size")

        def _parse_track_length(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        track_length = _parse_track_length(d.pop("track_length"))

        created_at = isoparse(d.pop("created_at"))

        track_boundary_summary = cls(
            id=id,
            track_id=track_id,
            track_name=track_name,
            track_config_name=track_config_name,
            grid_size=grid_size,
            track_length=track_length,
            created_at=created_at,
        )

        track_boundary_summary.additional_properties = d
        return track_boundary_summary

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
