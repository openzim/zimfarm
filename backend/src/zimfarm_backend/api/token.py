import datetime
from typing import Any

import jwt

from zimfarm_backend.api.constants import (
    JWT_SECRET,
    JWT_TOKEN_EXPIRY_DURATION,
    JWT_TOKEN_ISSUER,
)


def generate_access_token(
    *,
    user_id: str,
    username: str,
    issue_time: datetime.datetime,
    email: str | None = None,
    scope: dict[str, Any] | None = None,
) -> str:
    """Generate a JWT access token for the given user ID with configured expiry."""

    expire_time = issue_time + datetime.timedelta(seconds=JWT_TOKEN_EXPIRY_DURATION)
    payload = {
        "iss": JWT_TOKEN_ISSUER,  # issuer
        "exp": expire_time.timestamp(),  # expiration time
        "iat": issue_time.timestamp(),  # issued at
        "subject": user_id,
        "user": {
            "username": username,
            "email": email,
            "scope": scope or {},
        },
    }
    return jwt.encode(payload, key=JWT_SECRET, algorithm="HS256")
