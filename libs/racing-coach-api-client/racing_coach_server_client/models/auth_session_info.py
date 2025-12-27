from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="AuthSessionInfo")


@_attrs_define
class AuthSessionInfo:
    """Information about an active session.

    Attributes:
        session_id (str):
        user_agent (None | str):
        ip_address (None | str):
        created_at (datetime.datetime):
        last_active_at (datetime.datetime):
        is_current (bool | Unset):  Default: False.
    """

    session_id: str
    user_agent: None | str
    ip_address: None | str
    created_at: datetime.datetime
    last_active_at: datetime.datetime
    is_current: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        session_id = self.session_id

        user_agent: None | str
        user_agent = self.user_agent

        ip_address: None | str
        ip_address = self.ip_address

        created_at = self.created_at.isoformat()

        last_active_at = self.last_active_at.isoformat()

        is_current = self.is_current

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "session_id": session_id,
                "user_agent": user_agent,
                "ip_address": ip_address,
                "created_at": created_at,
                "last_active_at": last_active_at,
            }
        )
        if is_current is not UNSET:
            field_dict["is_current"] = is_current

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        session_id = d.pop("session_id")

        def _parse_user_agent(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        user_agent = _parse_user_agent(d.pop("user_agent"))

        def _parse_ip_address(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        ip_address = _parse_ip_address(d.pop("ip_address"))

        created_at = isoparse(d.pop("created_at"))

        last_active_at = isoparse(d.pop("last_active_at"))

        is_current = d.pop("is_current", UNSET)

        auth_session_info = cls(
            session_id=session_id,
            user_agent=user_agent,
            ip_address=ip_address,
            created_at=created_at,
            last_active_at=last_active_at,
            is_current=is_current,
        )

        auth_session_info.additional_properties = d
        return auth_session_info

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
