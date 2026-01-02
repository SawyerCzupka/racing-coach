from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TrackBoundaryUploadResponse")


@_attrs_define
class TrackBoundaryUploadResponse:
    """Response model for track boundary upload endpoint.

    Attributes:
        message (str): Human-readable status message
        boundary_id (str): UUID of the created/updated boundary
        track_name (str): Name of the track from IBT file
        track_config_name (None | str): Track configuration name
        status (str | Unset): Upload status Default: 'success'.
        replaced_existing (bool | Unset): Whether an existing boundary was replaced Default: False.
    """

    message: str
    boundary_id: str
    track_name: str
    track_config_name: None | str
    status: str | Unset = "success"
    replaced_existing: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        boundary_id = self.boundary_id

        track_name = self.track_name

        track_config_name: None | str
        track_config_name = self.track_config_name

        status = self.status

        replaced_existing = self.replaced_existing

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "boundary_id": boundary_id,
                "track_name": track_name,
                "track_config_name": track_config_name,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status
        if replaced_existing is not UNSET:
            field_dict["replaced_existing"] = replaced_existing

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        boundary_id = d.pop("boundary_id")

        track_name = d.pop("track_name")

        def _parse_track_config_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        track_config_name = _parse_track_config_name(d.pop("track_config_name"))

        status = d.pop("status", UNSET)

        replaced_existing = d.pop("replaced_existing", UNSET)

        track_boundary_upload_response = cls(
            message=message,
            boundary_id=boundary_id,
            track_name=track_name,
            track_config_name=track_config_name,
            status=status,
            replaced_existing=replaced_existing,
        )

        track_boundary_upload_response.additional_properties = d
        return track_boundary_upload_response

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
