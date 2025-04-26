from racing_coach.config.types.telemetry import TelemetryFrame, LapTelemetry
import pandas as pd


TEST_FILE = "../data_out/telemetry/f4_algarve_20250102_135623/telemetry_107.5115966796875_2025-01-02T14_06_35.772625.parquet"

# Load the parquet file
df = pd.read_parquet(TEST_FILE)

print(df)
