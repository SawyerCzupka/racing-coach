"""
Telemetry source implementations.

This package provides different telemetry sources for the racing coach client:
- LiveTelemetrySource: Real-time telemetry from iRacing SDK
- ReplayTelemetrySource: Playback from IBT telemetry files
"""

from .base import (
    TelemetryConnectionError,
    TelemetryReadError,
    TelemetrySource,
    TelemetrySourceError,
)
from .live import LiveTelemetrySource
from .replay import ReplayTelemetrySource

__all__ = [
    "TelemetrySource",
    "TelemetrySourceError",
    "TelemetryConnectionError",
    "TelemetryReadError",
    "LiveTelemetrySource",
    "ReplayTelemetrySource",
]
