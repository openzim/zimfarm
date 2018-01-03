from time import time
from flask import Blueprint, request, Response
from werkzeug.security import check_password_hash

from utils.mongo import Users
from utils.token import JWT
from utils.token import Type as TokenType
from .errors import BadRequest, Unauthorized


blueprint = Blueprint('auth', __name__, url_prefix='/api/auth')


@blueprint.route("/authorize", methods=["POST"])
def authorize():
    """
    Authorize a user with username and password
    :return: token
    """
    username = request.headers.get('username')
    password = request.headers.get('password')

    if username is None or password is None:
        raise BadRequest()

    user = Users().find_one({'username': username})
    if user is None:
        raise Unauthorized()

    is_valid = check_password_hash(user['password_hash'], password)
    if not is_valid:
        raise Unauthorized()

    jwt = JWT(username, TokenType.USER, user['is_admin'], time())
    return jwt.encoded()


@blueprint.route("/token", methods=["POST"])
def token():
    """
    Renew a token

    **Required:**
    Header token: the token to validate

    :return: new token if validation success
    :raises InvalidRequest: if token is not set in Header
    :raises AuthFailed: if username embedded in token does not exist
    :raise jwt.exceptions.ExpiredSignatureError: if token expired
    """
    jwt = JWT.decode(request.headers.get('token'))
    if jwt is None:
        raise BadRequest()

    user = Users().find_one({'username': jwt.username})
    if user is None:
        raise Unauthorized()
    jwt.is_admin = user['is_admin']
    jwt.issue_time = time()

    return jwt.encoded()


@blueprint.route("/validate", methods=["GET"])
def validate():
    """
    Validate a token

    **Required:**
    Header token: the token to validate

    :return: a flask response with code 200 if validation success
    :raises InvalidRequest: if token is not set in Header
    :raises AuthFailed: if username embedded in token does not exist
    :raise jwt.exceptions.ExpiredSignatureError: if token expired
    """
    jwt = JWT.decode(request.headers.get('token'))
    if jwt is None:
        raise BadRequest()

    user = Users().find_one({'username': jwt.username})
    if user is None:
        raise Unauthorized()

    return Response(status=200)
