import time
import uuid
import jwt
import flask
from routes.error.exception import InvalidRequest


class JWT:
    secret = 'secret'

    def __init__(self, encoded: str):
        self.payload = jwt.decode(encoded, self.secret, algorithms=['HS256'])

    @classmethod
    def encode(cls, payload) -> str:
        return jwt.encode(payload, cls.secret, algorithm='HS256').decode()

    @classmethod
    def from_request_header(cls, request: flask.request):
        token = request.headers.get('token')
        if token is None:
            raise InvalidRequest()
        else:
            return cls(token)

    @property
    def issuer(self) -> str:
        return self.payload['iss']

    @property
    def issue_time(self) -> str:
        return self.payload['iat']

    @property
    def expiration_time(self) -> str:
        return self.payload['exp']

    @property
    def identifier(self) -> str:
        return self.payload['jti']


class UserJWT(JWT):
    @classmethod
    def new(cls, username: str, scope: str):
        time_stamp = int(time.time())
        return cls.encode({
            'iss': 'dispatcher-backend',
            'exp': time_stamp + 60 * 30,
            'iat': time_stamp,
            'jti': str(uuid.uuid4()),
            'username': username,
            'scope': scope
        })

    @staticmethod
    def scope_is_valid(scope):
        return scope == 'administrator' or scope == 'worker'

    @property
    def username(self) -> str:
        return self.payload['username']

    @property
    def scope(self) -> str:
        return self.payload['scope']

    @property
    def is_admin(self) -> bool:
        return self.scope == 'administrator'


class MWOfflinerTaskJWT(JWT):
    @classmethod
    def new(cls):
        time_stamp = int(time.time())
        return cls.encode({
            'iss': 'dispatcher-backend',
            'exp': time_stamp + 60 * 60 * 24 * 7,
            'iat': time_stamp,
            'jti': str(uuid.uuid4()),
            'task_name': 'zimfarm.mwoffliner',
        })

    @property
    def task_name(self) -> str:
        return self.payload['task_name']
