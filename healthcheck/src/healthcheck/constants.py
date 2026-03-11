import datetime
import os
from typing import Any

from humanfriendly import parse_timespan


def getenv(key: str, *, mandatory: bool = False, default: Any = None) -> Any:
    value = os.getenv(key) or default

    if mandatory and not value:
        raise OSError(f"Please set the {key} environment variable")

    return value


def parse_bool(value: Any) -> bool:
    """Parse value into boolean."""
    return str(value).lower() in ("true", "1", "yes", "y", "on")


DEBUG = parse_bool(getenv("DEBUG", default="false"))

REQUESTS_TIMEOUT = parse_timespan(getenv("REQUESTS_TIMEOUT", default="1m"))

ZIMFARM_API_URL = getenv("ZIMFARM_API_URL", default="https://api.farm.openzim.org/v2")
ZIMFARM_FRONTEND_URL = getenv(
    "ZIMFARM_FRONTEND_URL", default="https://farm.openzim.org"
)
ZIMFARM_USERNAME = getenv("ZIMFARM_USERNAME", mandatory=True)
ZIMFARM_PASSWORD = getenv("ZIMFARM_PASSWORD", mandatory=True)
ZIMFARM_DATABASE_URL = getenv("ZIMFARM_DATABASE_URL", mandatory=True)

CMS_API_URL = getenv("CMS_API_URL", default="https://api.cms.openzim.org/v1")
CMS_ENABLED = parse_bool(getenv("CMS_ENABLED", default="false"))
CMS_PENDING_THRESHOLD = datetime.timedelta(
    seconds=parse_timespan(getenv("CMS_PENDING_THRESHOLD", default="24h"))
)
