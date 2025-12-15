from humanfriendly import parse_timespan

from zimfarm_backend.common.constants import getenv, parse_bool

# JWT settings
JWT_TOKEN_ISSUER = getenv("JWT_TOKEN_ISSUER", default="zimfarm_backend")
JWT_SECRET = getenv("JWT_SECRET", mandatory=True)
JWT_TOKEN_EXPIRY_DURATION = parse_timespan(
    getenv("JWT_TOKEN_EXPIRY_DURATION", default="1d")
)
ZIM_ILLUSTRATION_SIZE = int(getenv("ZIM_ILLUSTRATION_SIZE", default="48"))

AUTH_MODES: list[str] = getenv(
    "AUTH_MODES", default="local,oauth-oidc,oauth-session"
).split(",")

# OAuth/OIDC configuration
OAUTH_JWKS_URI = getenv(
    "OAUTH_JWKS_URI",
    default="https://login.kiwix.org/.well-known/jwks.json",
)
OAUTH_ISSUER = getenv("OAUTH_ISSUER", default="https://login.kiwix.org")
OAUTH_OIDC_CLIENT_ID = getenv(
    "OAUTH_OIDC_CLIENT_ID", default="d87a31d2-874e-44c4-9dc2-63fad523bf1b"
)
OAUTH_OIDC_LOGIN_REQUIRE_2FA = parse_bool(
    getenv("OAUTH_OIDC_LOGIN_REQUIRE_2FA", default="true")
)
OAUTH_SESSION_AUDIENCE_ID = getenv(
    "OAUTH_SESSION_AUDIENCE_ID", default="d87a31d2-874e-44c4-9dc2-63fad523bf1b"
)
OAUTH_SESSION_LOGIN_REQUIRE_2FA = parse_bool(
    getenv("OAUTH_SESSION_LOGIN_REQUIRE_2FA", default="true")
)
CREATE_NEW_OAUTH_ACCOUNT = parse_bool(
    getenv("CREATE_NEW_OAUTH_ACCOUNT", default="true")
)
