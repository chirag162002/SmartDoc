import logging
import sys
from app.core.config import settings

def setup_logging() -> logging.Logger:
    """
    Configures standard Python logging with structured formatting across SmartDoc backend services.
    """
    log_level_str = getattr(settings, "LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger("smartdoc")
    logger.setLevel(log_level)
    
    if not logger.handlers:
        logger.addHandler(handler)

    # Avoid duplicate propagation to root logger handlers
    logger.propagate = False

    return logger

logger = setup_logging()
