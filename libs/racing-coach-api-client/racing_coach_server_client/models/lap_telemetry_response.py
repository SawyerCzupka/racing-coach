from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.telemetry_frame_response import TelemetryFrameResponse


T = TypeVar("T", bound="LapTelemetryResponse")


@_attrs_define
class LapTelemetryResponse:
    """Response model for lap telemetry endpoint.

    Attributes:
        lap_id (str): UUID of the lap
        session_id (str): UUID of the session
        lap_number (int): Lap number
        frame_count (int): Number of telemetry frames
        frames (list[TelemetryFrameResponse]): Telemetry frames
    """

    lap_id: str
    session_id: str
    lap_number: int
    frame_count: int
    frames: list[TelemetryFrameResponse]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        lap_id = self.lap_id

        session_id = self.session_id

        lap_number = self.lap_number

        frame_count = self.frame_count

        frames = []
        for frames_item_data in self.frames:
            frames_item = frames_item_data.to_dict()
            frames.append(frames_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "lap_id": lap_id,
                "session_id": session_id,
                "lap_number": lap_number,
                "frame_count": frame_count,
                "frames": frames,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.telemetry_frame_response import TelemetryFrameResponse

        d = dict(src_dict)
        lap_id = d.pop("lap_id")

        session_id = d.pop("session_id")

        lap_number = d.pop("lap_number")

        frame_count = d.pop("frame_count")

        frames = []
        _frames = d.pop("frames")
        for frames_item_data in _frames:
            frames_item = TelemetryFrameResponse.from_dict(frames_item_data)

            frames.append(frames_item)

        lap_telemetry_response = cls(
            lap_id=lap_id,
            session_id=session_id,
            lap_number=lap_number,
            frame_count=frame_count,
            frames=frames,
        )

        lap_telemetry_response.additional_properties = d
        return lap_telemetry_response

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
