from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="DeviceAuthorizationStatus")


@_attrs_define
class DeviceAuthorizationStatus:
    """Response model for checking device authorization status.

    Attributes:
        device_name (str):
        status (str):
        created_at (datetime.datetime):
        expires_at (datetime.datetime):
    """

    device_name: str
    status: str
    created_at: datetime.datetime
    expires_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        device_name = self.device_name

        status = self.status

        created_at = self.created_at.isoformat()

        expires_at = self.expires_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "device_name": device_name,
                "status": status,
                "created_at": created_at,
                "expires_at": expires_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        device_name = d.pop("device_name")

        status = d.pop("status")

        created_at = isoparse(d.pop("created_at"))

        expires_at = isoparse(d.pop("expires_at"))

        device_authorization_status = cls(
            device_name=device_name,
            status=status,
            created_at=created_at,
            expires_at=expires_at,
        )

        device_authorization_status.additional_properties = d
        return device_authorization_status

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
