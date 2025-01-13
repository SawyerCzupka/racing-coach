"""
Telemetry collector class for iRacing.
"""

import logging
import time
from datetime import datetime
from typing import Callable

import irsdk

from racing_coach.config.types.telemetry import TelemetryFrame, LapTelemetry

logger = logging.getLogger(__name__)


class TelemetryCollector:
    def __init__(self):
        """Initialize the telemetry collector."""
        self.ir: irsdk.IRSDK | None = None
        self.ir_connected: bool = False
        self.last_time: float = time.time()
        self.running: bool = False

        self.data_buffer: list[TelemetryFrame] = []
        self.data_buffer2: list[TelemetryFrame] = []
        self.last_lap_number = -1

        self._lap_subscribers: list[Callable[[LapTelemetry], None]] = []

    def add_lap_completed_callback(
        self, callback: Callable[[LapTelemetry], None]
    ) -> None:
        """Subscribe to lap completed events."""
        self._lap_subscribers.append(callback)

    def notify_subscribers(self, lap: LapTelemetry) -> None:
        """Notify subscribers of a lap completion."""
        for subscriber in self._lap_subscribers:
            try:
                subscriber(lap)
            except Exception as e:
                logger.error(f"Error in lap subscriber callback: {e}")


    def connect(self) -> bool:
        """Initialize connection to iRacing."""
        self.ir = irsdk.IRSDK()
        return self._check_connection()

    def _check_connection(self) -> bool:
        """Check and manage iRacing connection state.

        Taken from the iRacing telemetry collector example"""
        if self.ir_connected and not (self.ir.is_initialized and self.ir.is_connected):
            self.ir_connected = False
            self.ir.shutdown()
            logger.info("IRSDK disconnected")
            return False

        elif (
            not self.ir_connected
            and self.ir.startup()
            and self.ir.is_initialized
            and self.ir.is_connected
        ):
            self.ir_connected = True
            logger.info("IRSDK connected")
            return True

        return self.ir_connected

    def collect_frame(self):
        """Collect a single frame of telemetry data."""
        if not self.ir_connected:
            return None

        self.ir.freeze_var_buffer_latest()

        frame = TelemetryFrame.from_irsdk(self.ir, datetime.now())

        if frame.lap_number != self.last_lap_number:
            logger.info(f"New lap: {frame.lap_number}")
            # New lap, save and reset the buffer. Save the telemetry to a json file.

            if self.last_lap_number != -1:
                last_time = frame.last_lap_time
                # self.save_data(last_time)

            self.last_lap_number = frame.lap_number
            self.data_buffer = []

        self.data_buffer.append(frame)

        return True

    def start(self):
        """Main loop for collecting telemetry data."""
        if not self.connect():
            logger.error("Failed to connect to iRacing")
            return

        self.running = True
        try:
            while self.running:
                if not self._check_connection():
                    time.sleep(1)
                    continue

                self.collect_frame()

        except KeyboardInterrupt:
            logger.info("Stopping telemetry collection")
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
    collector.start()


if __name__ == "__main__":
    main()
