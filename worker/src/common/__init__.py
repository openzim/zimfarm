import datetime
import logging

from common.constants import DEBUG

logger = logging.getLogger("worker")

if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s: %(levelname)s] %(message)s"))
    logger.addHandler(handler)


def getnow():
    """naive UTC now"""
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
