import json
import uuid
import string
import random
from datetime import datetime, timedelta

import jwt
from bson.objectid import ObjectId


class AccessToken:
    secret = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(32)])
    issuer = 'dispatcher'

    class JSONEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, datetime):
                return int(o.timestamp())
            elif isinstance(o, ObjectId):
                return str(o)
            elif isinstance(o, uuid.UUID):
                return str(o)
            else:
                super().default(o)

    @classmethod
    def encode(cls, user_id: ObjectId, username: str, scope: dict) -> str:
        issue_time = datetime.now()
        expire_time = issue_time + timedelta(minutes=60)
        payload = {
            'iss': cls.issuer,
            'exp': expire_time,
            'iat': issue_time,
            'jti': uuid.uuid4(),
            'user': {
                '_id': user_id,
                'username': username,
                'scope': scope
            }
        }
        return jwt.encode(payload, key=cls.secret, algorithm='HS256', json_encoder=cls.JSONEncoder).decode('utf-8')

    @classmethod
    def decode(cls, token: str) -> dict:
        return jwt.decode(token, cls.secret, algorithms=['HS256'])
