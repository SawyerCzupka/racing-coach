from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.lap_telemetry import LapTelemetry
    from ..models.session_frame import SessionFrame


T = TypeVar("T", bound="BodyUploadLapApiV1TelemetryLapPost")


@_attrs_define
class BodyUploadLapApiV1TelemetryLapPost:
    """
    Attributes:
        lap (LapTelemetry):
        session (SessionFrame): Frame of data pertaining to a session.
    """

    lap: LapTelemetry
    session: SessionFrame
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        lap = self.lap.to_dict()

        session = self.session.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "lap": lap,
                "session": session,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.lap_telemetry import LapTelemetry
        from ..models.session_frame import SessionFrame

        d = dict(src_dict)
        lap = LapTelemetry.from_dict(d.pop("lap"))

        session = SessionFrame.from_dict(d.pop("session"))

        body_upload_lap_api_v1_telemetry_lap_post = cls(
            lap=lap,
            session=session,
        )

        body_upload_lap_api_v1_telemetry_lap_post.additional_properties = d
        return body_upload_lap_api_v1_telemetry_lap_post

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
