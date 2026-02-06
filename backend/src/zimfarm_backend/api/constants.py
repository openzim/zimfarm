from humanfriendly import parse_timespan

from zimfarm_backend.common.constants import getenv, parse_bool

# JWT settings
JWT_TOKEN_ISSUER = getenv("JWT_TOKEN_ISSUER", default="zimfarm_backend")
JWT_SECRET = getenv("JWT_SECRET", mandatory=True)
JWT_TOKEN_EXPIRY_DURATION = parse_timespan(
    getenv("JWT_TOKEN_EXPIRY_DURATION", default="1d")
)
ZIM_ILLUSTRATION_SIZE = int(getenv("ZIM_ILLUSTRATION_SIZE", default="48"))

# List of authentication modes. Allowed values are "local", "oauth-oidc",
# "oauth-session"
AUTH_MODES: list[str] = getenv(
    "AUTH_MODES",
    default="local",
).split(",")

# OAuth/OIDC configuration
OAUTH_JWKS_URI = getenv(
    "OAUTH_JWKS_URI",
    default="https://login.kiwix.org/.well-known/jwks.json",
)
OAUTH_ISSUER = getenv("OAUTH_ISSUER", default="https://login.kiwix.org")
OAUTH_OIDC_CLIENT_ID = getenv(
    "OAUTH_OIDC_CLIENT_ID", default="38302485-7f3d-4e88-b1b3-ec02fb92ec8c"
)
OAUTH_OIDC_LOGIN_REQUIRE_2FA = parse_bool(
    getenv("OAUTH_OIDC_LOGIN_REQUIRE_2FA", default="true")
)
OAUTH_SESSION_AUDIENCE_ID = getenv(
    "OAUTH_SESSION_AUDIENCE_ID", default="bada4130-5143-4524-a0bb-0d69671beee2"
)
OAUTH_SESSION_LOGIN_REQUIRE_2FA = parse_bool(
    getenv("OAUTH_SESSION_LOGIN_REQUIRE_2FA", default="true")
)
CREATE_NEW_OAUTH_ACCOUNT = parse_bool(
    getenv("CREATE_NEW_OAUTH_ACCOUNT", default="true")
)
