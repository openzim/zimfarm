from bson import ObjectId
from flask import Blueprint, request, Response, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from utils.mongo import Users
from utils.token import JWT
from . import errors


blueprint = Blueprint('user', __name__, url_prefix='/api/user')


@blueprint.route("/", methods=["GET"])
def users():
    """
    List all users
    Only admins can access this API

    :raises BadRequest: if token is not set in Header
    :raises Unauthorized: if token expired
    :raises NotEnoughPrivilege: if user is not admin
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
        'meta': {'limit': limit, 'offset': offset},
        'items': users
    })


@blueprint.route("/<string:user_id>", methods=["GET", "PATCH"])
def user(user_id):
    """
    Single user API, you can:
    - Get detail
    - Change password
    - TODO: Change username
    - TODO: Change email

    :raises BadRequest: if token is not set in Header
    :raises Unauthorized: if token expired
    :raises NotFound: if user does not exist
    """

    # check token exist and is valid
    jwt = JWT.decode(request.headers.get('token'))
    if jwt is None:
        raise errors.BadRequest()

    if request.method == 'GET':
        user = Users().find_one({'_id': ObjectId(user_id)}, projection={'password_hash': False})
        if user is None:
            raise errors.NotFound()
        else:
            return jsonify(user)
    elif request.method == 'PATCH':
        # only admins can perform PATCH operation on another user
        if jwt.user_id != user_id and not jwt.is_admin:
            raise errors.NotEnoughPrivilege()

        user = Users().find_one({'_id': ObjectId(user_id)})
        if user is None:
            raise errors.NotFound()

        password_old = request.form.get('password_old')
        password_new = request.form.get('password_new')

        is_valid = check_password_hash(user['password_hash'], password_old)
        if not is_valid:
            raise errors.Unauthorized()

        Users().update_one({'_id': ObjectId(user_id)},
                           {'$set': {'password_hash': generate_password_hash(password_new)}})



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