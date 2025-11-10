from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_CONNECTION_STR: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"


settings = Settings()
