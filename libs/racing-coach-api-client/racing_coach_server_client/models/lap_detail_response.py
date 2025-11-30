from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="LapDetailResponse")


@_attrs_define
class LapDetailResponse:
    """Response model for lap detail endpoint.

    Attributes:
        lap_id (str): UUID of the lap
        session_id (str): UUID of the session
        lap_number (int): Lap number in the session
        lap_time (float | None): Lap time in seconds
        is_valid (bool): Whether the lap is valid
        track_name (str): Name of the track
        track_config_name (None | str): Track configuration name
        car_name (str): Name of the car
        has_metrics (bool): Whether metrics have been computed
        created_at (datetime.datetime): When the lap was recorded
    """

    lap_id: str
    session_id: str
    lap_number: int
    lap_time: float | None
    is_valid: bool
    track_name: str
    track_config_name: None | str
    car_name: str
    has_metrics: bool
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        lap_id = self.lap_id

        session_id = self.session_id

        lap_number = self.lap_number

        lap_time: float | None
        lap_time = self.lap_time

        is_valid = self.is_valid

        track_name = self.track_name

        track_config_name: None | str
        track_config_name = self.track_config_name

        car_name = self.car_name

        has_metrics = self.has_metrics

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "lap_id": lap_id,
                "session_id": session_id,
                "lap_number": lap_number,
                "lap_time": lap_time,
                "is_valid": is_valid,
                "track_name": track_name,
                "track_config_name": track_config_name,
                "car_name": car_name,
                "has_metrics": has_metrics,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        lap_id = d.pop("lap_id")

        session_id = d.pop("session_id")

        lap_number = d.pop("lap_number")

        def _parse_lap_time(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        lap_time = _parse_lap_time(d.pop("lap_time"))

        is_valid = d.pop("is_valid")

        track_name = d.pop("track_name")

        def _parse_track_config_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        track_config_name = _parse_track_config_name(d.pop("track_config_name"))

        car_name = d.pop("car_name")

        has_metrics = d.pop("has_metrics")

        created_at = isoparse(d.pop("created_at"))

        lap_detail_response = cls(
            lap_id=lap_id,
            session_id=session_id,
            lap_number=lap_number,
            lap_time=lap_time,
            is_valid=is_valid,
            track_name=track_name,
            track_config_name=track_config_name,
            car_name=car_name,
            has_metrics=has_metrics,
            created_at=created_at,
        )

        lap_detail_response.additional_properties = d
        return lap_detail_response

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
