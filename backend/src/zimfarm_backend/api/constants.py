from humanfriendly import parse_timespan

from zimfarm_backend.common.constants import getenv, parse_bool

# JWT settings
JWT_TOKEN_ISSUER = getenv("JWT_TOKEN_ISSUER", default="zimfarm_backend")
JWT_SECRET = getenv("JWT_SECRET", mandatory=True)
JWT_TOKEN_EXPIRY_DURATION = parse_timespan(
    getenv("JWT_TOKEN_EXPIRY_DURATION", default="1d")
)
ZIM_ILLUSTRATION_SIZE = int(getenv("ZIM_ILLUSTRATION_SIZE", default="48"))

# Kiwix OAuth/OIDC configuration
KIWIX_JWKS_URI = getenv(
    "KIWIX_JWKS_URI",
    default="https://login.kiwix.org/.well-known/jwks.json",
)
KIWIX_ISSUER = getenv("KIWIX_ISSUER", default="https://login.kiwix.org")
KIWIX_CLIENT_ID = getenv(
    "KIWIX_CLIENT_ID", default="d87a31d2-874e-44c4-9dc2-63fad523bf1b"
)
CREATE_NEW_KIWIX_ACCOUNT = parse_bool(
    getenv("CREATE_NEW_KIWIX_ACCOUNT", default="true")
)
