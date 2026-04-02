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
# Authentication mode: can be either "local" or "oauth"
AUTH_MODE = getenv("AUTH_MODE", default="local")
ZIMFARM_USERNAME = getenv("ZIMFARM_USERNAME", default="")
ZIMFARM_PASSWORD = getenv("ZIMFARM_PASSWORD", default="")
ZIMFARM_OAUTH_ISSUER = getenv(
    "ZIMFARM_OAUTH_ISSUER", default="https://ory.login.kiwix.org"
)
ZIMFARM_OAUTH_CLIENT_ID = getenv("ZIMFARM_OAUTH_CLIENT_ID", default="")
ZIMFARM_OAUTH_CLIENT_SECRET = getenv("ZIMFARM_OAUTH_CLIENT_SECRET", default="")
ZIMFARM_OAUTH_AUDIENCE_ID = getenv("ZIMFARM_OAUTH_AUDIENCE_ID", default="")
ZIMFARM_TOKEN_RENEWAL_WINDOW = datetime.timedelta(
    seconds=parse_timespan(getenv("ZIMFARM_TOKEN_RENEWAL_WINDOW", default="5m"))
)
ZIMFARM_DATABASE_URL = getenv("ZIMFARM_DATABASE_URL", mandatory=True)

CMS_API_URL = getenv("CMS_API_URL", default="https://api.cms.openzim.org/v1")
CMS_ENABLED = parse_bool(getenv("CMS_ENABLED", default="false"))
CMS_PENDING_THRESHOLD = datetime.timedelta(
    seconds=parse_timespan(getenv("CMS_PENDING_THRESHOLD", default="24h"))
)
