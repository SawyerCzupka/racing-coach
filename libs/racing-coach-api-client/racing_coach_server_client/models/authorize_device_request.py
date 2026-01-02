from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AuthorizeDeviceRequest")


@_attrs_define
class AuthorizeDeviceRequest:
    """Request model for authorizing a device (from web UI).

    Attributes:
        user_code (str):
        approve (bool | Unset):  Default: True.
    """

    user_code: str
    approve: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_code = self.user_code

        approve = self.approve

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_code": user_code,
            }
        )
        if approve is not UNSET:
            field_dict["approve"] = approve

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_code = d.pop("user_code")

        approve = d.pop("approve", UNSET)

        authorize_device_request = cls(
            user_code=user_code,
            approve=approve,
        )

        authorize_device_request.additional_properties = d
        return authorize_device_request

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
