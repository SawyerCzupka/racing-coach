"""Configuration settings for Racing Coach Server."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    alembic_url: str = "postgresql://postgres:postgres@timescaledb:5432/postgres"  # Non-async
    debug: bool = False


settings = Settings()
