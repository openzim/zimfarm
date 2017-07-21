import time, uuid
import jwt
import flask
from routes.error.exception import InvalidRequest


class JWT:
    secret = 'secret'

    def __init__(self, encoded: str):
        self.payload = jwt.decode(encoded, self.secret, algorithms=['HS256'])

    @staticmethod
    def from_request_header(request: flask.request):
        token = request.headers.get('token')
        if token is None:
            raise InvalidRequest()
        else:
            return JWT(token)

    @classmethod
    def new(cls, username: str, scope: str):
        time_stamp = int(time.time())
        return jwt.encode({
            'iss': 'dispatcher-backend',
            'exp': time_stamp + 60 * 30,
            'iat': time_stamp,
            'jti': str(uuid.uuid4()),
            'username': username,
            'scope': scope
        }, cls.secret, algorithm='HS256').decode()

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
