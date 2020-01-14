from functools import wraps
from typing import Union

from flask import request
from jwt import exceptions as jwt_exceptions
from bson.objectid import ObjectId, InvalidId

from utils.token import AccessToken
from .errors import Unauthorized, NotEnoughPrivilege

API_PATH = "/v1"


def token_from_request(request):
    if "token" in request.headers:
        token = request.headers["token"]
    elif "Authorization" in request.headers:
        token = request.headers["Authorization"]
    else:
        token = None
    if token:
        token_parts = token.split(" ")
        if len(token_parts) > 1:
            token = token_parts[1]
    payload = AccessToken.decode(token)
    return AccessToken.Payload(payload)


def authenticate(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            kwargs["token"] = token_from_request(request)
            return f(*args, **kwargs)
        except jwt_exceptions.ExpiredSignatureError:
            raise Unauthorized("token expired")
        except (jwt_exceptions.InvalidTokenError, jwt_exceptions.PyJWTError):
            raise Unauthorized("token invalid")

    return wrapper


def require_perm(namespace: str, perm_name: str):
    def decorate(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = kwargs.get("token")
            if not token:
                raise Unauthorized("token missing")
            if not token.get_permission(namespace, perm_name):
                raise NotEnoughPrivilege(f"{namespace}.{perm_name}")
            return f(*args, **kwargs)

        return wrapper

    return decorate


def auth_info_if_supplied(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        kwargs["token"] = None
        try:
            kwargs["token"] = token_from_request(request)
        except jwt_exceptions.ExpiredSignatureError:
            kwargs["token"] = None
        except (jwt_exceptions.InvalidTokenError, jwt_exceptions.PyJWTError):
            kwargs["token"] = None
        return f(*args, **kwargs)

    return wrapper


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
