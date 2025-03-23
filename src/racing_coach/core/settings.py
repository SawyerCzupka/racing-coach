from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELEMETRY_OUTPUT_DIR: str = "./data_out/telemetry"

    TELEM_SAMPLE: str = "data_out/telemetry/telemetry_SAMPLE2.parquet"

    # Database
    DB_CONNECTION_STRING: str = (
        "postgresql://postgres:postgres@localhost:5432/racing_telemetry"
    )
    DB_ENABLED: bool = True
    DB_BATCH_SIZE: int = 60  # Number of telemetry frames to batch before committing

    # Braking
    BRAKE_ZONE_MIN_PCT: float = 0.05  # 0.1 = 10%
    BRAKE_ZONE_SEP_TIME: float = 2.5  # seconds


def get_settings():
    return Settings()


settings = Settings()
