import urllib.error
from flask import Blueprint, request, Response, jsonify

from utils.mongo import Users
from utils.token import JWT
from . import errors


blueprint = Blueprint('user', __name__, url_prefix='/api/user')


@blueprint.route("/", methods=["GET"])
def users():
    """
    List all users
    Only admins can access this api
    """

    # check token exist and is valid
    jwt = JWT.decode(request.headers.get('token'))
    if jwt is None:
        raise errors.BadRequest()

    # only admins can enqueue task
    if not jwt.is_admin:
        raise errors.NotEnoughPrivilege()

    limit = request.args.get('limit', 10)
    offset = request.args.get('limit', 0)

    cursor = Users().find(skip=offset, limit=limit, projection={'password_hash': False})
    users = [user for user in cursor]

    return jsonify({
        'meta': {
            'limit': limit,
            'offset': offset
        },
        'items': users
    })


@blueprint.route("/<string:user_id>", methods=["GET"])
def user(user_id):
    """

    :return:
    """

    # check token exist and is valid
    jwt = JWT.decode(request.headers.get('token'))
    if jwt is None:
        raise errors.BadRequest()

    if request.method == 'GET':
        user = Users().find_one({'_id': user_id}, projection={'password_hash': False})
        return jsonify(user)





#
# @blueprint.route("/<string:username>", methods=["PUT", "GET", "DELETE"])
# def user(username):
#     token = UserJWT.from_request_header(request)
#
#     if request.method == 'PUT':
#         json = request.get_json()
#         password = json.get('password')
#         scope = json.get('scope')
#
#         if password is None and scope is None:
#             raise exception.InvalidRequest()
#
#         if username == token.username:
#             # everyone could PUT self
#             if password is not None:
#                 update_rabbitmq_user(username, password)
#             user = upsert_user(username, password, scope)
#         else:
#             # non admin users cannot PUT other users
#             if not token.is_admin:
#                 raise exception.NotEnoughPrivilege()
#
#             # check username is valid
#             if username == getenv('DISPATCHER_USERNAME'):
#                 raise exception.UsernameNotValid()
#
#             user_exists = Users().find_one({'username': username}) is not None
#
#             # when creating a new user, have to provide password
#             if not user_exists and password is None:
#                 raise exception.UserDoesNotExist()
#
#             # when creating a new user, use default scope if non provided
#             if not user_exists and scope is None:
#                 scope = {}
#
#             if password is not None:
#                 update_rabbitmq_user(username, password)
#             user = upsert_user(username, password, scope)
#
#         return jsonify(user)
#     elif request.method == 'GET':

#     elif request.method == 'DELETE':
#         result = Users().delete_one({'username': username})
#         if result.deleted_count == 1:
#             delete_rabbitmq_user(username)
#             return Response(status=204)
#         else:
#             return Response(status=404)
#
#
# def upsert_user(username: str, password: str=None, scope: dict=None):
#     filter = {'username': username}
#
#     set = {}
#     if password is not None:
#         set['password_hash'] = generate_password_hash(password)
#     if scope is not None:
#         set['scope'] = JWT.validate_scope(scope)
#
#     return Users().find_one_and_update(filter, {'$set': set}, {'_id': False, 'password_hash': False},
#                                                  return_document=ReturnDocument.AFTER, upsert=True)


def update_rabbitmq_user(username: str, password: str):
    try:
        status_code = rabbitmq.put_user(username, password, 'worker')
        if status_code >= 300:
            raise errors.RabbitMQPutUserFailed(status_code)
        status_code = rabbitmq.put_permission('zimfarm', username)
        if status_code >= 300:
            raise errors.RabbitMQPutPermissionFailed(status_code)
    except urllib.error.HTTPError as error:
        code = error.getcode()
        raise errors.RabbitMQError(code)


def delete_rabbitmq_user(username: str):
    try:
        status_code = rabbitmq.delete_user(username)
        if status_code >= 300:
            raise errors.RabbitMQDeleteUserFailed(status_code)
    except urllib.error.HTTPError as error:
        code = error.getcode()
        raise errors.RabbitMQError(code)
