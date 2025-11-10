"""
Factory for creating telemetry sources.

This module provides a factory function that creates the appropriate
telemetry source based on the application configuration.
"""

import logging
from pathlib import Path

from racing_coach_client.config import Settings

from .sources import LiveTelemetrySource, ReplayTelemetrySource, TelemetrySource

logger = logging.getLogger(__name__)


def create_telemetry_source(settings: Settings) -> TelemetrySource:
    """
    Create a telemetry source based on configuration settings.

    This factory function reads the application settings and instantiates
    the appropriate telemetry source (live or replay).

    Args:
        settings: Application settings containing telemetry configuration.

    Returns:
        TelemetrySource: Configured telemetry source instance.

    Raises:
        ValueError: If configuration is invalid (e.g., replay mode without file path).
        FileNotFoundError: If replay file is specified but doesn't exist.

    Examples:
        >>> settings = Settings(TELEMETRY_MODE="live")
        >>> source = create_telemetry_source(settings)
        >>> isinstance(source, LiveTelemetrySource)
        True

        >>> settings = Settings(
        ...     TELEMETRY_MODE="replay",
        ...     REPLAY_FILE_PATH="telemetry.ibt"
        ... )
        >>> source = create_telemetry_source(settings)
        >>> isinstance(source, ReplayTelemetrySource)
        True
    """
    mode = settings.TELEMETRY_MODE.lower()

    if mode == "live":
        logger.info("Creating live telemetry source (iRacing SDK)")
        return LiveTelemetrySource()

    elif mode == "replay":
        if not settings.REPLAY_FILE_PATH:
            raise ValueError("REPLAY_FILE_PATH must be set when TELEMETRY_MODE is 'replay'")

        file_path = Path(settings.REPLAY_FILE_PATH)
        if not file_path.exists():
            raise FileNotFoundError(f"Replay telemetry file not found: {settings.REPLAY_FILE_PATH}")

        logger.info(
            f"Creating replay telemetry source: {settings.REPLAY_FILE_PATH} "
            f"(speed: {settings.REPLAY_SPEED}x, loop: {settings.REPLAY_LOOP})"
        )

        return ReplayTelemetrySource(
            file_path=file_path,
            speed_multiplier=settings.REPLAY_SPEED,
            loop=settings.REPLAY_LOOP,
        )

    else:
        raise ValueError(f"Invalid TELEMETRY_MODE: '{mode}'. Must be 'live' or 'replay'.")
