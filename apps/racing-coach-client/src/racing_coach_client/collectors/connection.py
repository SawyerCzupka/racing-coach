import logging

import irsdk

logger = logging.getLogger(__name__)


class iRacingConnectionManager:
    def __init__(self):
        self.ir: irsdk.IRSDK | None = None
        self.ir_connected: bool = False

    def connect(self) -> bool:
        self.ir = irsdk.IRSDK()
        return self._check_connection()

    def _check_connection(self) -> bool:
        if not self.ir:
            return False

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

    def is_connected(self) -> bool:
        return self.ir_connected and self.ir is not None

    def get_ir(self) -> irsdk.IRSDK:
        if not self.is_connected() or not self.ir:
            raise RuntimeError("get_ir() called while not connected to iRacing")

        return self.ir

    def disconnect(self):
        if self.ir:
            self.ir.shutdown()

        self.ir_connected = False
        self.ir = None

    def ensure_connected(self):
        if not self.is_connected():
            return self.connect()

        return self._check_connection()
