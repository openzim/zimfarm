import os
from typing import Any

from humanfriendly import parse_timespan


def getenv(key: str, *, mandatory: bool = False, default: Any = None) -> Any:
    value = os.getenv(key, default=default)

    if mandatory and not value:
        raise OSError(f"Please set the {key} environment variable")

    return value


class Settings:
    """
    Settings for the Zimfarm Dispatcher Backend.
    """

    POSTGRES_URI = getenv("POSTGRES_URI", mandatory=True)

    # JWT settings
    JWT_TOKEN_ISSUER = getenv("JWT_TOKEN_ISSUER", default="zimfarm_backend")
    JWT_SECRET = getenv("JWT_SECRET", mandatory=True)
    JWT_TOKEN_EXPIRY_DURATION = parse_timespan(
        getenv("JWT_TOKEN_EXPIRY_DURATION", default="1d")
    )
    REFRESH_TOKEN_EXPIRY_DURATION = parse_timespan(
        getenv("REFRESH_TOKEN_EXPIRY_DURATION", default="30d")
    )
