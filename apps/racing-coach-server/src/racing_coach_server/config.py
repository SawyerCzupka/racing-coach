"""Configuration settings for Racing Coach Server."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    debug: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
