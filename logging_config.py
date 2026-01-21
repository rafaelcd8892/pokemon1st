"""
Logging configuration for Pokemon Gen 1 Battle Simulator.

Usage:
    from logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Message")
"""

import logging
import sys
from pathlib import Path

# Log levels mapped to names for configuration
LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}

# Default configuration
DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FORMAT_SIMPLE = '%(levelname)s: %(message)s'
LOG_FILE = Path(__file__).parent / 'logs' / 'pokemon_battle.log'

_initialized = False


def setup_logging(
    level: int = DEFAULT_LOG_LEVEL,
    log_to_file: bool = False,
    log_file: Path = LOG_FILE,
    simple_format: bool = True
) -> None:
    """
    Configure the logging system.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_to_file: Whether to also log to a file
        log_file: Path to the log file
        simple_format: Use simple format (no timestamps) for console
    """
    global _initialized

    if _initialized:
        return

    # Create logs directory if needed
    if log_to_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = LOG_FORMAT_SIMPLE if simple_format else LOG_FORMAT
    console_handler.setFormatter(logging.Formatter(console_format))
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_to_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(file_handler)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given module name.

    Args:
        name: Usually __name__ of the calling module

    Returns:
        Configured logger instance
    """
    # Ensure logging is set up
    if not _initialized:
        setup_logging()

    return logging.getLogger(name)


def set_log_level(level: int | str) -> None:
    """
    Change the log level at runtime.

    Args:
        level: Logging level (int or string like 'debug', 'info')
    """
    if isinstance(level, str):
        level = LOG_LEVELS.get(level.lower(), DEFAULT_LOG_LEVEL)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.setLevel(level)
