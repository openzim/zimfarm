from uuid import uuid4
from flask import request, Response, jsonify
import database.user
import jwt, utils
from .exceptions import InvalidRequest, AuthFailed


def login():
    try:
        username = request.headers.get('username')
        password = request.headers.get('password')
        old_token = request.headers.get('token')

        if (username is None or password is None) and (old_token is None):
            raise InvalidRequest()

        if username is not None and password is not None:
            if database.user.is_valid(username, password):
                return jsonify({'success': True, 'token': new_user_token(username)})
            else:
                raise AuthFailed()
        elif old_token is not None:
            utils.jwt_decode(old_token)
            return jsonify({'success': True, 'token': new_user_token(username)})
        else:
            raise InvalidRequest()
    except InvalidRequest:
        return Response(status=400)
    except AuthFailed:
        return jsonify({'error': 'Username or password invalid'}), 401
    except (jwt.DecodeError, jwt.ExpiredSignatureError):
        return jsonify({'error': 'token invalid or expired'}), 401


def new_user_token(username: str):
    time_stamp = utils.utc_timestamp()
    return utils.jwt_encode({
        'iss': 'dispatcher-backend',
        'exp': time_stamp + 60 * 30,
        'iat': time_stamp,
        'jti': str(uuid4()),
        'username': username,
        'scope': ['dashboard', 'tasks']
    })
