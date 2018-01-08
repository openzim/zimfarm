import os
import uuid
from time import time
import jwt


class JWT:
    secret = os.getenv('JWT_SECRET', 'secret')
    issuer = 'dispatcher'

    def __init__(self, user_id: str, username: str, is_admin: bool):
        self.user_id = user_id
        self.username = username
        self.is_admin = is_admin

    def encoded(self) -> str:
        issue_time = int(time())
        delta = 60 * 60
        payload = {
            'iss': JWT.issuer,
            'exp': issue_time + delta,
            'iat': issue_time,
            'jti': str(uuid.uuid4()),
            'user_id': self.user_id,
            'username': self.username,
            'is_admin': self.is_admin
        }
        return jwt.encode(payload, JWT.secret, algorithm='HS256').decode()

    @classmethod
    def decode(cls, token: str):
        if token is None:
            return None
        payload = jwt.decode(token, JWT.secret, algorithms=['HS256'])
        return JWT(payload['user_id'], payload['username'], payload['is_admin'])
