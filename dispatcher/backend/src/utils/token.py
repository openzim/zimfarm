import json
import uuid
import string
import random
from datetime import datetime
from time import time
from typing import Optional

import jwt
from bson.objectid import ObjectId


class AccessToken:
    secret = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(32)])
    issuer = 'dispatcher'

    class JSONEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, datetime):
                return o.isoformat() + 'Z'
            elif isinstance(o, ObjectId):
                return str(o)
            elif isinstance(o, uuid.UUID):
                return str(o)
            else:
                super().default(o)

    @classmethod
    def encode(cls, user_id: ObjectId, username: str, scope: dict) -> str:
        issue_time = int(time())
        delta = 60 * 15  # access token expires in 15 minutes
        payload = {
            'iss': cls.issuer,
            'exp': issue_time + delta,
            'iat': issue_time,
            'jti': uuid.uuid4(),
            'user_id': user_id,
            'username': username,
            'scope': scope
        }
        return jwt.encode(payload, key=cls.secret, algorithm='HS256', json_encoder=cls.JSONEncoder).decode('utf-8')

    @classmethod
    def decode(cls, token: str) -> Optional[dict]:
        if token is None:
            return None
        else:
            try:
                payload = jwt.decode(token, cls.secret, algorithms=['HS256'])
            except jwt.exceptions.InvalidTokenError:
                return None
            return payload


class RefreshToken:
    pass
