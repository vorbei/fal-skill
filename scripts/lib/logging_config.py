import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(name: str = "fal-skill", level: str = None):
    """Configure logging for fal-skill"""

    # Get log level from environment or parameter
    if level is None:
        level = os.environ.get('FAL_LOG_LEVEL', 'INFO')

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console_fmt = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console.setFormatter(console_fmt)
    logger.addHandler(console)

    # File handler (optional, only if log directory exists)
    log_dir = os.path.expanduser("~/.config/fal-skill/logs")
    try:
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'fal-skill.log'),
            maxBytes=1_000_000,  # 1MB
            backupCount=3
        )
        file_handler.setLevel(logging.DEBUG)  # Always debug in file
        file_fmt = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)
    except (OSError, PermissionError):
        # If we can't create log directory, just use console
        pass

    return logger
