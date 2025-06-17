from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVER_URL: str = "http://localhost:8000"
    LAP_COMPLETION_THRESHOLD: float = (
        95.0  # Percentage of lap distance to consider lap complete
    )


settings = Settings()
