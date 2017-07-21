from flask import Blueprint, request, jsonify

import database.user
from utils.token import JWT
from .error.exception import InvalidRequest, AuthFailed


blueprint = Blueprint('auth', __name__, url_prefix='/auth')


@blueprint.route("/login", methods=["POST"])
def login():
    username = request.headers.get('username')
    password = request.headers.get('password')

    if username is None or password is None:
        raise InvalidRequest()

    user = database.user.get(username)
    if user is None:
        raise AuthFailed()

    is_valid = user.is_password_valid(password)
    if not is_valid:
        raise AuthFailed()

    return jsonify({'token': JWT.new(username, user.scope)})


@blueprint.route("/renew", methods=["POST"])
def renew():
    old_jwt = JWT.from_request_header(request)
    return jsonify({'token': JWT.new(old_jwt.username, old_jwt.scope)})
