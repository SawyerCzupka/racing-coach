"""
Telemetry collector class for iRacing.
"""

import logging
import time
from datetime import datetime
from typing import Literal, Optional
from pathlib import Path

import irsdk
import pandas as pd

from racing_coach.config.settings import settings
from racing_coach.config.types.telemetry import TelemetryFrame

logger = logging.getLogger(__name__)


class TelemetryCollector:
    def __init__(self):
        """Initialize the telemetry collector."""
        self.ir: Optional[irsdk.IRSDK] = None
        self.ir_connected: bool = False
        self.last_time: float = time.time()
        self.frame_count: int = 0
        self.running: bool = False

        self.data_buffer: list[TelemetryFrame] = []
        self.data_buffer2: list[TelemetryFrame] = []
        self.last_lap_number = -1

        self.session_car = "f4"
        self.session_track = "algarve"

        # self.session_base_name = "f4_laguna_"
        self.session_base_name = f"{self.session_car}_{self.session_track}_"
        self.session_name = ""

    def connect(self) -> bool:
        """Initialize connection to iRacing."""
        self.ir = irsdk.IRSDK()
        return self._check_connection()

    def _check_connection(self) -> bool:
        """Check and manage iRacing connection state.

        Taken from the iracing telemetry collector example"""
        if self.ir_connected and not (self.ir.is_initialized and self.ir.is_connected):
            self.ir_connected = False
            self.ir.shutdown()
            print("irsdk disconnected")
            return False

        elif (
            not self.ir_connected
            and self.ir.startup()
            and self.ir.is_initialized
            and self.ir.is_connected
        ):
            self.ir_connected = True
            print("irsdk connected")
            return True

        return self.ir_connected

    def save_data(
        self, lap_time: int = 0, format: Literal["json", "parquet"] = "parquet"
    ):
        """Save the data buffer to a json file."""
        logger.info(f"Saving telemetry data to {format}")

        if not self.data_buffer:
            return

        match format:
            case "json":
                self._save_data_json()
            case "parquet":
                self._save_data_parquet(lap_time=lap_time)
            case _:
                raise ValueError(f"Unsupported format: {format}")

    def _save_data_parquet(
        self, lap_time: int = 0, output_dir=settings.TELEMETRY_OUTPUT_DIR
    ):
        """Save the data buffer to a parquet file."""
        if not self.session_name:
            self.session_name = self.session_base_name + datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

        output_dir = Path(output_dir) / self.session_name

        # output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().isoformat().replace(":", "_")
        output_file = f"{output_dir}/telemetry_{lap_time}_{timestamp}.parquet"

        # Save the data buffer to a parquet file
        df = pd.DataFrame([data.model_dump() for data in self.data_buffer])
        df.to_parquet(output_file)

    def _save_data_json(self, output_dir=settings.TELEMETRY_OUTPUT_DIR):
        """Save the data buffer to a json file."""
        output_file = f"{output_dir}/telemetry_{datetime.now().isoformat()}.json"

        # Save the data buffer to a json file
        # with open(output_file, "w") as f:
        #     for data in self.data_buffer:
        #         f.write(data.json() + "\n")

    def collect_frame(self):
        """Collect a single frame of telemetry data."""
        if not self.ir_connected:
            return None

        self.ir.freeze_var_buffer_latest()

        data = TelemetryFrame.from_irsdk(self.ir, datetime.now())

        if data.lap_number != self.last_lap_number:
            logger.info(f"New lap: {data.lap_number}")
            # New lap, save and reset the buffer. Save the telemetry to a json file.

            if self.last_lap_number != -1:
                last_time = data.last_lap_time
                self.save_data(last_time)

            self.last_lap_number = data.lap_number
            self.data_buffer = []

        self.data_buffer.append(data)

        # Here you can add actual data collection when needed
        # For now, we're just monitoring the rate
        return True

    def run(self):
        """Main loop for collecting telemetry data."""
        if not self.connect():
            print("Failed to connect to iRacing")
            return

        self.running = True
        try:
            while self.running:
                if not self._check_connection():
                    time.sleep(1)
                    continue

                self.collect_frame()

        except KeyboardInterrupt:
            print("\nStopping telemetry collection")
        finally:
            self.stop()

    def stop(self):
        """Stop the telemetry collector."""
        self.running = False
        if self.ir:
            self.ir.shutdown()
        self.ir_connected = False


def main():
    collector = TelemetryCollector()
    collector.run()


if __name__ == "__main__":
    main()
