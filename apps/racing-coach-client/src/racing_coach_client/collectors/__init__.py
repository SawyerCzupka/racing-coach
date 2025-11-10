"""
Telemetry collectors package.

This package provides telemetry collection functionality for iRacing,
including support for live telemetry and replay from IBT files.
"""

from .factory import create_telemetry_source
from .iracing import TelemetryCollector
from .sources import (
    LiveTelemetrySource,
    ReplayTelemetrySource,
    TelemetryConnectionError,
    TelemetryReadError,
    TelemetrySource,
    TelemetrySourceError,
)

__all__ = [
    "TelemetryCollector",
    "create_telemetry_source",
    "TelemetrySource",
    "TelemetrySourceError",
    "TelemetryConnectionError",
    "TelemetryReadError",
    "LiveTelemetrySource",
    "ReplayTelemetrySource",
]
