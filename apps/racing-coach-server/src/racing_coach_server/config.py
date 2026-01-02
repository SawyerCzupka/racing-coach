"""Configuration settings for Racing Coach Server."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    alembic_url: str = "postgresql://postgres:postgres@timescaledb:5432/postgres"  # Non-async
    debug: bool = False

    # Auth settings
    session_cookie_secure: bool = True  # Set to False for local development without HTTPS
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    web_session_duration_days: int = 30
    device_token_duration_days: int = 365
    device_auth_expiration_minutes: int = 15
    web_app_url: str = "http://localhost:3000"  # URL of the web dashboard
    marketing_site_url: str = "http://localhost:4321"  # URL of the marketing site

    # CORS settings - comma-separated list of allowed origins
    cors_origins: str = "http://localhost:3000,http://localhost:4321"


settings = Settings()
