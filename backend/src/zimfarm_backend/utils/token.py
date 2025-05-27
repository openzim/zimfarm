import datetime

import jwt

from zimfarm_backend.settings import Settings


def generate_access_token(user_id: str) -> str:
    """Generate an access token for a user"""

    issue_time = datetime.datetime.now(datetime.UTC)
    expire_time = issue_time + datetime.timedelta(
        seconds=Settings.JWT_TOKEN_EXPIRY_DURATION
    )
    payload = {
        "iss": Settings.JWT_TOKEN_ISSUER,  # issuer
        "exp": expire_time.timestamp(),  # expiration time
        "iat": issue_time.timestamp(),  # issued at
        "subject": user_id,
    }
    return jwt.encode(payload, key=Settings.JWT_SECRET, algorithm="HS256")
