import os
import uuid
from enum import Enum
from time import time, localtime
import jwt


class Type(Enum):
    USER = 'user'
    UPLOAD = 'upload'


class JWT:
    secret = os.getenv('SECRET', 'secret')
    issuer = 'dispatcher'

    def __init__(self, username: str, type: Type, is_admin: bool, issue_time: time):
        self.username = username
        self.type = type
        self.is_admin = is_admin
        self.issue_time = issue_time

    def encoded(self) -> str:
        issue_time = int(self.issue_time)
        if self.type == Type.USER:
            delta = 60 * 60
        elif self.type == Type.UPLOAD:
            delta = 60 * 60 * 24
        else:
            delta = 0
        payload = {
            'iss': JWT.issuer,
            'exp': issue_time + delta,
            'iat': issue_time,
            'jti': str(uuid.uuid4()),
            'username': self.username,
            'type': self.type.value,
            'is_admin': self.is_admin
        }
        return jwt.encode(payload, JWT.secret, algorithm='HS256').decode()

    @classmethod
    def decode(cls, token: str):
        if token is None:
            return None
        payload = jwt.decode(token, JWT.secret, algorithms=['HS256'])
        # TODO: check issuer against JWT.issuer
        return JWT(payload['username'], Type(payload['type']), payload['is_admin'], issue_time=localtime(payload['iat']))


# class _JWT:
#     @property
#     def issuer(self) -> str:
#         return self.payload['iss']
#
#     @property
#     def issue_time(self) -> str:
#         return self.payload['iat']
#
#     @property
#     def expiration_time(self) -> str:
#         return self.payload['exp']
#
#     @property
#     def identifier(self) -> str:
#         return self.payload['jti']
#
#     @property
#     def username(self) -> str:
#         return self.payload['username']
#
#     @property
#     def type(self) -> str:
#         return self.payload['token_type']
#
#     @property
#     def is_admin(self) -> bool:
#         return self.payload['is_admin']
#
#
