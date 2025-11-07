import logging

from zimfarm_backend.common.constants import DEBUG

logger = logging.getLogger("zimfarm_backend")

if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s: %(levelname)s] %(message)s"))
    logger.addHandler(handler)
