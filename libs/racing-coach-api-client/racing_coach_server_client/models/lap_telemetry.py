from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.telemetry_frame import TelemetryFrame


T = TypeVar("T", bound="LapTelemetry")


@_attrs_define
class LapTelemetry:
    """
    Attributes:
        frames (list[TelemetryFrame]):
        lap_time (float | None): Total lap time in seconds
    """

    frames: list[TelemetryFrame]
    lap_time: float | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        frames = []
        for frames_item_data in self.frames:
            frames_item = frames_item_data.to_dict()
            frames.append(frames_item)

        lap_time: float | None
        lap_time = self.lap_time

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "frames": frames,
                "lap_time": lap_time,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.telemetry_frame import TelemetryFrame

        d = dict(src_dict)
        frames = []
        _frames = d.pop("frames")
        for frames_item_data in _frames:
            frames_item = TelemetryFrame.from_dict(frames_item_data)

            frames.append(frames_item)

        def _parse_lap_time(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        lap_time = _parse_lap_time(d.pop("lap_time"))

        lap_telemetry = cls(
            frames=frames,
            lap_time=lap_time,
        )

        lap_telemetry.additional_properties = d
        return lap_telemetry

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
