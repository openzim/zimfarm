import datetime
import json
import os
import random
import string
import uuid

import jwt

import db.models as dbm
from common import getnow, to_naive_utc
from common.constants import TOKEN_EXPIRY
from routes import errors


class AccessToken:
    secret = os.getenv(
        "JWT_SECRET",
        "".join(
            [random.choice(string.ascii_letters + string.digits) for _ in range(32)]
        ),
    )
    issuer = "dispatcher"
    expire_time_delta = datetime.timedelta(hours=TOKEN_EXPIRY)

    class JSONEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, datetime.datetime):
                return int(o.timestamp())
            if isinstance(o, uuid.UUID):
                return str(o)
            super().default(o)

    class Payload:
        def __init__(self, data: dict):
            self._data = data
            try:
                self._data["user"]["_id"] = uuid.UUID(self._data["user"]["_id"])
            except ValueError:
                raise errors.Unauthorized()

        @property
        def user_id(self) -> uuid:
            return self._data["user"]["_id"]

        @property
        def username(self) -> str:
            return self._data["user"]["username"]

        @property
        def email(self) -> str:
            return self._data["user"].get("email", None)

        def get_permission(self, namespace: str, name: str, default: bool = False):
            return self._data["user"]["scope"].get(namespace, {}).get(name, default)

    @classmethod
    def encode_db(cls, user: dbm.User) -> str:
        return cls.encode(
            {
                "_id": str(user.id),
                "email": user.email,
                "username": user.username,
                "scope": user.scope,
            }
        )

    @classmethod
    def encode(cls, user: dict) -> str:
        issue_time = getnow()
        expire_time = issue_time + cls.expire_time_delta
        payload = {
            "iss": cls.issuer,  # issuer
            "exp": expire_time,  # expiration time
            "iat": issue_time,  # issued at
            # "jti": uuid.uuid4(),  # JWT ID
            "user": user,  # user payload (username, scope)
        }
        return jwt.encode(
            payload, key=cls.secret, algorithm="HS256", json_encoder=cls.JSONEncoder
        )

    @classmethod
    def decode(cls, token: str) -> dict:
        return jwt.decode(token, cls.secret, algorithms=["HS256"])

    @classmethod
    def get_expiry(cls, token: str) -> datetime:
        return to_naive_utc(cls.decode(token)["exp"])


class LoadedAccessToken(AccessToken):
    def __init__(self, user_id: uuid.UUID, username: str, scope: dict):
        self.user_id = user_id
        self.username = username
        self.scope = scope

    def encode(self):
        return super().encode(
            {"_id": self.user_id, "username": self.username, "scope": self.scope}
        )

    @classmethod
    def decode(cls, token: str) -> "LoadedAccessToken":
        payload = super().decode(token)
        user = payload.get("user", {})
        return cls(
            user_id=user.get("_id"),
            username=user.get("username"),
            scope=user.get("scope"),
        )
