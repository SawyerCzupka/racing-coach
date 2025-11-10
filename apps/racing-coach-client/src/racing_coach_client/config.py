from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings for the racing coach client.

    Settings can be configured via environment variables or .env file.
    All settings are prefixed with the app name when using environment variables.
    """

    # Server configuration
    SERVER_URL: str = "http://localhost:8000"

    # Lap processing configuration
    LAP_COMPLETION_THRESHOLD: float = 95.0
    """Percentage of lap distance to consider lap complete"""

    # Telemetry source configuration
    TELEMETRY_MODE: Literal["live", "replay"] = "replay"
    """Telemetry mode: 'live' for iRacing SDK, 'replay' for IBT files"""

    REPLAY_FILE_PATH: str | None = None
    """Path to IBT telemetry file (required when TELEMETRY_MODE='replay')"""

    REPLAY_SPEED: float = 1.0
    """Playback speed multiplier for replay mode (1.0 = real-time, 2.0 = 2x speed)"""

    REPLAY_LOOP: bool = False
    """Whether to loop replay when reaching the end of the file"""

    # Collection configuration
    COLLECTION_RATE_HZ: int = 60
    """Target telemetry collection rate in Hz"""


settings = Settings()
