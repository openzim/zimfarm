from humanfriendly import parse_timespan

from zimfarm_backend.common.constants import getenv

# JWT settings
JWT_TOKEN_ISSUER = getenv("JWT_TOKEN_ISSUER", default="zimfarm_backend")
JWT_SECRET = getenv("JWT_SECRET", mandatory=True)
JWT_TOKEN_EXPIRY_DURATION = parse_timespan(
    getenv("JWT_TOKEN_EXPIRY_DURATION", default="1d")
)
ZIM_ILLUSTRATION_SIZE = int(getenv("ZIM_ILLUSTRATION_SIZE", default="48"))
