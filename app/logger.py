import sys
from loguru import logger

def serialize(record):
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "extra": record["extra"],
    }
    return subset

def configure_logging():
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
        serialize=True, # Enable JSON serialization
    )

configure_logging()
