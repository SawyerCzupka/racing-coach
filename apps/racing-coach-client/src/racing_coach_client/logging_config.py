"""
Logging configuration module for racing coach client.

Provides colored console logging with configurable formatting that shows
module names and uses ANSI color codes for different log levels.
"""

import logging
import sys
from typing import Any


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds ANSI color codes to log messages.

    Colors are applied based on log level:
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Bold Red
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[1;31m",  # Bold Red
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    def __init__(self, fmt: str | None = None, datefmt: str | None = None, use_color: bool = True):
        """
        Initialize the colored formatter.

        Args:
            fmt: Log message format string
            datefmt: Date format string
            use_color: Whether to use ANSI color codes
        """
        super().__init__(fmt, datefmt)
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with colors.

        Args:
            record: The log record to format

        Returns:
            Formatted log message with color codes
        """
        if not self.use_color:
            return super().format(record)

        # Save original levelname
        levelname = record.levelname

        # Color the level name
        if levelname in self.COLORS:
            colored_levelname = f"{self.COLORS[levelname]}{levelname:<8}{self.RESET}"
            record.levelname = colored_levelname

        # Format the message
        result = super().format(record)

        # Restore original levelname
        record.levelname = levelname

        return result


def setup_logging(
    level: str = "INFO",
    use_color: bool = True,
    show_module: bool = True,
) -> None:
    """
    Configure application logging with custom formatting.

    This function sets up the root logger with a colored console handler
    and the specified log level.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_color: Whether to use colored output
        show_module: Whether to show module names in log output
    """
    # Determine format string based on whether to show module
    if show_module:
        # Format: timestamp - [module] - LEVEL - message
        log_format = "%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"
    else:
        # Format: timestamp - LEVEL - message
        log_format = "%(asctime)s - %(levelname)s - %(message)s"

    # Create formatter
    formatter = ColoredFormatter(
        fmt=log_format,
        datefmt="%H:%M:%S",  # Only show time, not date
        use_color=use_color,
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Reduce noise from verbose third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
