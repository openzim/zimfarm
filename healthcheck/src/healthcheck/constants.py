from pathlib import Path

from humanfriendly import parse_timespan

from healthcheck import getenv

REQUESTS_TIMEOUT = parse_timespan(getenv("REQUESTS_TIMEOUT", default="1m"))

ZIMFARM_API_URL = getenv("ZIMFARM_API_URL", mandatory=True)
ZIMFARM_USERNAME = getenv("ZIMFARM_USERNAME", mandatory=True)
ZIMFARM_PASSWORD = getenv("ZIMFARM_PASSWORD", mandatory=True)
ZIMFARM_DATABASE_URL = getenv("ZIMFARM_DATABASE_URL", mandatory=True)

CACHE_LOCATION = Path(getenv("CACHE_LOCATION", default="/data/cache"))
CACHE_KEY_PREFIX = getenv("CACHE_KEY_PREFIX", default="healthcheck")
DEFAULT_CACHE_TTL = parse_timespan(getenv("DEFAULT_CACHE_TTL", default="1m"))
