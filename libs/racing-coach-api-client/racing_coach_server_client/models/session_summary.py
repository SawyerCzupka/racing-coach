from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="SessionSummary")


@_attrs_define
class SessionSummary:
    """Summary of a session for listing purposes.

    Attributes:
        session_id (str): UUID of the session
        track_id (int): Track ID
        track_name (str): Name of the track
        track_config_name (None | str): Track configuration name
        track_type (str): Type of track
        car_id (int): Car ID
        car_name (str): Name of the car
        car_class_id (int): Car class ID
        series_id (int): Series ID
        lap_count (int): Number of laps in the session
        created_at (datetime.datetime): When the session was created
    """

    session_id: str
    track_id: int
    track_name: str
    track_config_name: None | str
    track_type: str
    car_id: int
    car_name: str
    car_class_id: int
    series_id: int
    lap_count: int
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        session_id = self.session_id

        track_id = self.track_id

        track_name = self.track_name

        track_config_name: None | str
        track_config_name = self.track_config_name

        track_type = self.track_type

        car_id = self.car_id

        car_name = self.car_name

        car_class_id = self.car_class_id

        series_id = self.series_id

        lap_count = self.lap_count

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "session_id": session_id,
                "track_id": track_id,
                "track_name": track_name,
                "track_config_name": track_config_name,
                "track_type": track_type,
                "car_id": car_id,
                "car_name": car_name,
                "car_class_id": car_class_id,
                "series_id": series_id,
                "lap_count": lap_count,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        session_id = d.pop("session_id")

        track_id = d.pop("track_id")

        track_name = d.pop("track_name")

        def _parse_track_config_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        track_config_name = _parse_track_config_name(d.pop("track_config_name"))

        track_type = d.pop("track_type")

        car_id = d.pop("car_id")

        car_name = d.pop("car_name")

        car_class_id = d.pop("car_class_id")

        series_id = d.pop("series_id")

        lap_count = d.pop("lap_count")

        created_at = isoparse(d.pop("created_at"))

        session_summary = cls(
            session_id=session_id,
            track_id=track_id,
            track_name=track_name,
            track_config_name=track_config_name,
            track_type=track_type,
            car_id=car_id,
            car_name=car_name,
            car_class_id=car_class_id,
            series_id=series_id,
            lap_count=lap_count,
            created_at=created_at,
        )

        session_summary.additional_properties = d
        return session_summary

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
