from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.lap_metrics import LapMetrics


T = TypeVar("T", bound="MetricsUploadRequest")


@_attrs_define
class MetricsUploadRequest:
    """Request model for uploading lap metrics.

    Attributes:
        lap_metrics (LapMetrics):
        lap_id (str):
    """

    lap_metrics: LapMetrics
    lap_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        lap_metrics = self.lap_metrics.to_dict()

        lap_id = self.lap_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "lap_metrics": lap_metrics,
                "lap_id": lap_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.lap_metrics import LapMetrics

        d = dict(src_dict)
        lap_metrics = LapMetrics.from_dict(d.pop("lap_metrics"))

        lap_id = d.pop("lap_id")

        metrics_upload_request = cls(
            lap_metrics=lap_metrics,
            lap_id=lap_id,
        )

        metrics_upload_request.additional_properties = d
        return metrics_upload_request

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
