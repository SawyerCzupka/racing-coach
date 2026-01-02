from __future__ import annotations

from collections.abc import Mapping
from io import BytesIO
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types
from ..types import UNSET, File, Unset

T = TypeVar("T", bound="BodyUploadTrackBoundary")


@_attrs_define
class BodyUploadTrackBoundary:
    """
    Attributes:
        file (File): IBT file containing boundary laps
        left_lap_number (int | Unset): Lap number for left boundary Default: 1.
        right_lap_number (int | Unset): Lap number for right boundary Default: 3.
        grid_size (int | Unset): Resolution of the boundary Default: 1000.
    """

    file: File
    left_lap_number: int | Unset = 1
    right_lap_number: int | Unset = 3
    grid_size: int | Unset = 1000
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file = self.file.to_tuple()

        left_lap_number = self.left_lap_number

        right_lap_number = self.right_lap_number

        grid_size = self.grid_size

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "file": file,
            }
        )
        if left_lap_number is not UNSET:
            field_dict["left_lap_number"] = left_lap_number
        if right_lap_number is not UNSET:
            field_dict["right_lap_number"] = right_lap_number
        if grid_size is not UNSET:
            field_dict["grid_size"] = grid_size

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("file", self.file.to_tuple()))

        if not isinstance(self.left_lap_number, Unset):
            files.append(("left_lap_number", (None, str(self.left_lap_number).encode(), "text/plain")))

        if not isinstance(self.right_lap_number, Unset):
            files.append(("right_lap_number", (None, str(self.right_lap_number).encode(), "text/plain")))

        if not isinstance(self.grid_size, Unset):
            files.append(("grid_size", (None, str(self.grid_size).encode(), "text/plain")))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file = File(payload=BytesIO(d.pop("file")))

        left_lap_number = d.pop("left_lap_number", UNSET)

        right_lap_number = d.pop("right_lap_number", UNSET)

        grid_size = d.pop("grid_size", UNSET)

        body_upload_track_boundary = cls(
            file=file,
            left_lap_number=left_lap_number,
            right_lap_number=right_lap_number,
            grid_size=grid_size,
        )

        body_upload_track_boundary.additional_properties = d
        return body_upload_track_boundary

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
