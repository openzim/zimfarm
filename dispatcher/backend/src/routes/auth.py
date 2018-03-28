from flask import Blueprint, request, Response, jsonify
from werkzeug.security import check_password_hash

from app import system_username, system_password
from utils.mongo import Users
from utils.token import AccessToken, RefreshToken
from .errors import BadRequest, Unauthorized


blueprint = Blueprint('auth', __name__, url_prefix='/api/auth')


@blueprint.route("/authorize", methods=["POST"])
def authorize():
    """
    Authorize a user with username and password
    When success, return json object with access and refresh token

    [Header] username
    [Header] password
    """

    # get username and password from request header
    username = request.headers.get('username')
    password = request.headers.get('password')
    if username is None or password is None:
        raise BadRequest()

    # check user exists
    user = Users().find_one({'username': username})
    if user is None:
        raise Unauthorized()

    # check password is valid
    is_valid = check_password_hash(user['password_hash'], password)
    if not is_valid:
        raise Unauthorized()

    # generate token
    access_token = AccessToken.encode(user_id=user['_id'], username=user['username'], scope=user['scope'])

    # send response
    response_json = {
        'access_token': access_token,
        'refresh_token': ''
    }
    response = jsonify(response_json)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    return response


@blueprint.route("/token", methods=["POST"])
def token():
    """
    Get a new set of access and refresh token after validating an old refresh token

    [Header] refresh_token
    """

    return Response()

    # jwt = JWT.decode(request.headers.get('token'))
    # if jwt is None:
    #     raise BadRequest()
    #
    # user = Users().find_one({'username': jwt.username})
    # if user is None:
    #     raise Unauthorized()
    #
    # jwt.is_admin = user['is_admin']
    # return jwt.encoded()


@blueprint.route("/validate", methods=["POST"])
def validate():
    """
    Validate an access token

    [Header] token: the access token to validate
    """
    payload = AccessToken.decode(request.headers.get('token'))
    if payload is None:
        raise Unauthorized()

    user = Users().find_one({'username': payload['username']})
    if user is None:
        raise Unauthorized()

    return Response()


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
