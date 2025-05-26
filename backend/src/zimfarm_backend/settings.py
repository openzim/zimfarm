import os
from typing import Any


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
