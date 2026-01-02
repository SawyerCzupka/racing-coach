from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="SessionFrame")


@_attrs_define
class SessionFrame:
    """Frame of data pertaining to a session.

    Attributes:
        track_id (int): Track ID
        track_name (str): Track name
        track_config_name (None | str): Track config name
        car_id (int): Car ID
        car_name (str): Car name
        car_class_id (int): Car class ID
        series_id (int): Series ID
        session_type (str): Session type
        timestamp (datetime.datetime | Unset): Timestamp of the session frame
        session_id (UUID | Unset): Session ID
        track_type (str | Unset): Track type Default: 'road course'.
    """

    track_id: int
    track_name: str
    track_config_name: None | str
    car_id: int
    car_name: str
    car_class_id: int
    series_id: int
    session_type: str
    timestamp: datetime.datetime | Unset = UNSET
    session_id: UUID | Unset = UNSET
    track_type: str | Unset = "road course"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        track_id = self.track_id

        track_name = self.track_name

        track_config_name: None | str
        track_config_name = self.track_config_name

        car_id = self.car_id

        car_name = self.car_name

        car_class_id = self.car_class_id

        series_id = self.series_id

        session_type = self.session_type

        timestamp: str | Unset = UNSET
        if not isinstance(self.timestamp, Unset):
            timestamp = self.timestamp.isoformat()

        session_id: str | Unset = UNSET
        if not isinstance(self.session_id, Unset):
            session_id = str(self.session_id)

        track_type = self.track_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "track_id": track_id,
                "track_name": track_name,
                "track_config_name": track_config_name,
                "car_id": car_id,
                "car_name": car_name,
                "car_class_id": car_class_id,
                "series_id": series_id,
                "session_type": session_type,
            }
        )
        if timestamp is not UNSET:
            field_dict["timestamp"] = timestamp
        if session_id is not UNSET:
            field_dict["session_id"] = session_id
        if track_type is not UNSET:
            field_dict["track_type"] = track_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        track_id = d.pop("track_id")

        track_name = d.pop("track_name")

        def _parse_track_config_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        track_config_name = _parse_track_config_name(d.pop("track_config_name"))

        car_id = d.pop("car_id")

        car_name = d.pop("car_name")

        car_class_id = d.pop("car_class_id")

        series_id = d.pop("series_id")

        session_type = d.pop("session_type")

        _timestamp = d.pop("timestamp", UNSET)
        timestamp: datetime.datetime | Unset
        if isinstance(_timestamp, Unset):
            timestamp = UNSET
        else:
            timestamp = isoparse(_timestamp)

        _session_id = d.pop("session_id", UNSET)
        session_id: UUID | Unset
        if isinstance(_session_id, Unset):
            session_id = UNSET
        else:
            session_id = UUID(_session_id)

        track_type = d.pop("track_type", UNSET)

        session_frame = cls(
            track_id=track_id,
            track_name=track_name,
            track_config_name=track_config_name,
            car_id=car_id,
            car_name=car_name,
            car_class_id=car_class_id,
            series_id=series_id,
            session_type=session_type,
            timestamp=timestamp,
            session_id=session_id,
            track_type=track_type,
        )

        session_frame.additional_properties = d
        return session_frame

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
