from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash

from mongo import UsersCollection
from utils.token import UserJWT
from .error.exception import InvalidRequest, AuthFailed


blueprint = Blueprint('auth', __name__, url_prefix='/auth')


@blueprint.route("/login", methods=["POST"])
def login():
    username = request.headers.get('username')
    password = request.headers.get('password')

    if username is None or password is None:
        raise InvalidRequest()

    user = UsersCollection().find_one({'username': username})
    if user is None:
        raise AuthFailed()

    is_valid = check_password_hash(user['password_hash'], password)
    if not is_valid:
        raise AuthFailed()

    return jsonify({'token': UserJWT.new(username)})


@blueprint.route("/renew", methods=["POST"])
def renew():
    old_jwt = UserJWT.from_request_header(request)
    return jsonify({'token': UserJWT.new(old_jwt.username, old_jwt.scope)})
