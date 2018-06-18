from functools import wraps
from typing import Optional
from flask import request
from jwt import exceptions as jwt_exceptions

from utils.token import AccessToken
from .errors import Unauthorized


def access_token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            token = request.headers.get('token', '')
            if token == '':
                raise Unauthorized('token invalid')
            token = AccessToken.decode(token)
            kwargs['access_token'] = token
            return f(*args, **kwargs)
        except jwt_exceptions.ExpiredSignatureError:
            raise Unauthorized('token expired')
        except jwt_exceptions.InvalidTokenError:
            raise Unauthorized('token invalid')
        except jwt_exceptions.PyJWTError:
            raise Unauthorized('token invalid')
    return wrapper


def bson_object_id(keys: list):
    def decorate(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return decorate
