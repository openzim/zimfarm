import json
import uuid
import string
import random
from datetime import datetime, timedelta

import jwt
from bson import ObjectId


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


class AccessControl:
    secret = AccessToken.secret
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

    def __init__(self, user_id: ObjectId, username: str, scope: dict):
        self.user_id = user_id
        self.username = username
        self.scope = scope

    def encode(self):
        issue_time = datetime.now()
        expire_time = issue_time + self.expire_time_delta
        payload = {
            'iss': self.issuer,
            'exp': expire_time,
            'iat': issue_time,
            'jti': uuid.uuid4(),
            'user': {
                '_id': self.user_id,
                'username': self.username,
                'scope': self.scope
            }
        }
        return jwt.encode(payload, key=self.secret, algorithm='HS256', json_encoder=self.JSONEncoder).decode('utf-8')

    @classmethod
    def decode(cls, token: str) -> 'AccessControl':
        payload = jwt.decode(token, cls.secret, algorithms=['HS256'])
        user = payload.get('user', {})
        return AccessControl(user_id=user.get('_id'), username=user.get('username'), scope=user.get('scope'))
