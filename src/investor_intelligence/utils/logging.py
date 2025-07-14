"""Logging configuration for Investor Intelligence Agent."""

import logging
import logging.handlers
from pathlib import Path
from .config import config


def setup_logging():
    """Set up logging configuration."""

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger("investor_intelligence")
    logger.setLevel(getattr(logging, config.logging.level))

    # Create formatters
    formatter = logging.Formatter(config.logging.format)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Create file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        config.logging.file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    file_handler.setLevel(getattr(logging, config.logging.level))
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Initialize logger
logger = setup_logging()
