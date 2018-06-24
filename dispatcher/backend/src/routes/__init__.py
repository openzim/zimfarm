from functools import wraps
from flask import request
from jwt import exceptions as jwt_exceptions
from bson.objectid import ObjectId, InvalidId

from utils.token import AccessToken
from .errors import Unauthorized


def authenticate(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            token = request.headers.get('token', None)
            user = AccessToken.decode(token).get('user', {})
            kwargs['user'] = user
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
            for key in keys:
                object_id = kwargs.get(key, None)
                if not isinstance(key, str):
                    continue
                try:
                    object_id = ObjectId(object_id)
                    kwargs[key] = object_id
                except InvalidId:
                    raise errors.BadRequest(message="Invalid ObjectID")
            return f(*args, **kwargs)
        return wrapper
    return decorate
