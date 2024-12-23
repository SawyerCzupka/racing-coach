from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TEST: str = ""
    TELEMETRY_OUTPUT_DIR: str = "./data_out/telemetry"


settings = Settings()
