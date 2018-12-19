from functools import wraps
from typing import Union

from flask import request
from jwt import exceptions as jwt_exceptions
from bson.objectid import ObjectId, InvalidId

from utils.token import AccessToken, AccessControl
from .errors import Unauthorized, NotEnoughPrivilege


# def authenticate(f):
#     @wraps(f)
#     def wrapper(*args, **kwargs):
#         try:
#             token = request.headers.get('token', None)
#             user = AccessToken.decode(token).get('user', {})
#             kwargs['user'] = user
#             return f(*args, **kwargs)
#         except jwt_exceptions.ExpiredSignatureError:
#             raise Unauthorized('token expired')
#         except (jwt_exceptions.InvalidTokenError, jwt_exceptions.PyJWTError):
#             raise Unauthorized('token invalid')
#     return wrapper


def authenticate2(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            if 'token' in request.headers:
                token = request.headers['token']
            elif 'Authorization' in request.headers:
                token = request.headers['Authorization']
                token_parts = token.split(' ')
                if len(token_parts) > 1:
                    token = token_parts[1]
            else:
                token = None
            payload = AccessToken.decode(token)
            kwargs['token'] = AccessToken.Payload(payload)
            return f(*args, **kwargs)
        except jwt_exceptions.ExpiredSignatureError:
            raise Unauthorized('token expired')
        except (jwt_exceptions.InvalidTokenError, jwt_exceptions.PyJWTError):
            raise Unauthorized('token invalid')
    return wrapper


def authenticate(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            token = request.headers.get('Authorization', '')
            token_parts = token.split(' ')
            if len(token_parts) > 1:
                token = token_parts[1]
            payload = AccessToken.decode(token)
            kwargs['token'] = AccessToken.Payload(payload)

            try:
                response = f(*args, **kwargs)
            except TypeError:
                kwargs.pop('token')
                response = f(*args, **kwargs)
            return response
        except jwt_exceptions.ExpiredSignatureError:
            raise Unauthorized('token expired')
        except (jwt_exceptions.InvalidTokenError, jwt_exceptions.PyJWTError):
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


def url_object_id(names: Union[list, str]):
    if isinstance(names, str):
        names = [names]
    def decorate(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            for name in names:
                try:
                    object_id = ObjectId(kwargs.get(name, None))
                    kwargs[name] = object_id
                except InvalidId:
                    pass
            return f(*args, **kwargs)
        return wrapper
    return decorate
