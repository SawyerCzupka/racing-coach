from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="UserResponse")


@_attrs_define
class UserResponse:
    """Response model for current user.

    Attributes:
        user_id (str):
        email (str):
        display_name (None | str):
        email_verified (bool):
        is_admin (bool):
        created_at (datetime.datetime):
    """

    user_id: str
    email: str
    display_name: None | str
    email_verified: bool
    is_admin: bool
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        email = self.email

        display_name: None | str
        display_name = self.display_name

        email_verified = self.email_verified

        is_admin = self.is_admin

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "email": email,
                "display_name": display_name,
                "email_verified": email_verified,
                "is_admin": is_admin,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = d.pop("user_id")

        email = d.pop("email")

        def _parse_display_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        display_name = _parse_display_name(d.pop("display_name"))

        email_verified = d.pop("email_verified")

        is_admin = d.pop("is_admin")

        created_at = isoparse(d.pop("created_at"))

        user_response = cls(
            user_id=user_id,
            email=email,
            display_name=display_name,
            email_verified=email_verified,
            is_admin=is_admin,
            created_at=created_at,
        )

        user_response.additional_properties = d
        return user_response

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
