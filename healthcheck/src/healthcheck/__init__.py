import datetime
import logging
import os
from typing import Any


def getenv(key: str, *, mandatory: bool = False, default: Any = None) -> Any:
    value = os.getenv(key) or default

    if mandatory and not value:
        raise OSError(f"Please set the {key} environment variable")

    return value


def parse_bool(value: Any) -> bool:
    """Parse value into boolean."""
    return str(value).lower() in ("true", "1", "yes", "y", "on")


logger = logging.getLogger("healthcheck")

if not logger.hasHandlers():
    logger.setLevel(
        logging.DEBUG if parse_bool(getenv("DEBUG", default="false")) else logging.INFO
    )
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s: %(levelname)s] %(message)s"))
    logger.addHandler(handler)


def getnow():
    """naive UTC now"""
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
