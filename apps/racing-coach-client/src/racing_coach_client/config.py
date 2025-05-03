from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVER_URL: str = "http://localhost:8000"


settings = Settings()
