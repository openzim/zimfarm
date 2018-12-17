import json
import uuid
import string
import random
from datetime import datetime, timedelta

import jwt
from bson.objectid import ObjectId, InvalidId


class AccessControl:
    secret = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(32)])
    issuer = 'dispatcher'
    expire_time_delta = timedelta(minutes=60)

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

    def __init__(self, user_id: ObjectId, username: str, scope):
        pass

    def encode(self):
        pass


class AccessToken:
    secret = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(32)])
    issuer = 'dispatcher'
    expire_time_delta = timedelta(minutes=60)

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

    class Payload:
        def __init__(self, data: dict):
            self._data = data
            self._data['user']['_id'] = ObjectId(self._data['user']['_id'])

        @property
        def user_id(self) -> ObjectId:
            return self._data['user']['_id']

        @property
        def username(self) -> ObjectId:
            return self._data['user']['username']

        @property
        def email(self) -> ObjectId:
            return self._data['user'].get('email', None)

        def get_permission(self, namespace: str, name: str, default: bool = False):
            return self._data['user']['scope'].get(namespace, {}).get(name, default)

    @classmethod
    def encode(cls, user: dict) -> str:
        issue_time = datetime.now()
        expire_time = issue_time + cls.expire_time_delta
        payload = {
            'iss': cls.issuer,
            'exp': expire_time,
            'iat': issue_time,
            'jti': uuid.uuid4(),
            'user': user
        }
        return jwt.encode(payload, key=cls.secret, algorithm='HS256', json_encoder=cls.JSONEncoder).decode('utf-8')

    @classmethod
    def decode(cls, token: str) -> dict:
        return jwt.decode(token, cls.secret, algorithms=['HS256'])
