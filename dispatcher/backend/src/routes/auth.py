from flask import Blueprint, request, Response
from werkzeug.security import check_password_hash

from app import system_username, system_password
from utils.mongo import Users
from utils.token import JWT
from .errors import BadRequest, Unauthorized


blueprint = Blueprint('auth', __name__, url_prefix='/api/auth')


@blueprint.route("/authorize", methods=["POST"])
def authorize():
    """
    Authorize a user with username and password

    :return: token
    """
    username = request.form.get('username')
    password = request.form.get('password')

    if username is None or password is None:
        raise BadRequest()

    user = Users().find_one({'username': username})
    if user is None:
        raise Unauthorized()

    is_valid = check_password_hash(user['password_hash'], password)
    if not is_valid:
        raise Unauthorized()

    jwt = JWT(user['_id'], user[Users.username], user['is_admin'])
    return jwt.encoded()


@blueprint.route("/token", methods=["POST"])
def token():
    """
    Renew a token

    **Required:**
    Header token: the token to validate

    :return: new token if validation success
    :raises BadRequest: if token is not set in Header
    :raises Unauthorized: if username embedded in token does not exist
    """
    jwt = JWT.decode(request.headers.get('token'))
    if jwt is None:
        raise BadRequest()

    user = Users().find_one({'username': jwt.username})
    if user is None:
        raise Unauthorized()

    jwt.is_admin = user['is_admin']
    return jwt.encoded()


@blueprint.route("/validate", methods=["POST"])
def validate():
    """
    Validate a token

    **Required:**
    Header token: the token to validate

    :return: a flask response with code 200 if validation success
    :raises BadRequest: if token is not set in Header
    :raises Unauthorized: if username embedded in token does not exist
    """
    jwt = JWT.decode(request.headers.get('token'))
    if jwt is None:
        raise BadRequest()

    user = Users().find_one({'username': jwt.username})
    if user is None:
        raise Unauthorized()

    return Response(status=200)


@blueprint.route("/rabbitmq/<string:intention>", methods=["POST"])
def rabbitmq_user(intention: str):
    """
    Handles RabbitMQ auth http backend request
    See also: https://github.com/rabbitmq/rabbitmq-auth-backend-http

    :param intention: the sub-path of the request
    :return Response: allow or deny the auth request
    """

    username = request.form.get('username')
    if username is None:
        return Response("deny")

    if intention == 'user':
        password = request.form.get('password')
        if username == system_username and password == system_password:
            return Response("allow")
        else:
            user = Users().find_one({'username': username}, {'password_hash': True, '_id': False})
            if user is not None and check_password_hash(user['password_hash'], password):
                return Response("allow")
            else:
                return Response("deny")
    elif intention == 'vhost' or intention == 'resource' or intention == 'topic':
        # print('/rabbitmq_log/{}: {}'.format(intention, request.form), file=sys.stderr)
        vhost = request.form.get('vhost')
        if username == system_username and vhost == 'zimfarm':
            return Response("allow")
        else:
            user = Users().find_one({'username': username}, {'_id': False})
            if user is not None and vhost == 'zimfarm':
                return Response("allow")
            else:
                return Response("deny")
    else:
        return Response("deny")
