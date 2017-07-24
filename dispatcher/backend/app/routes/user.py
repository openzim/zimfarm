import urllib.error
import sqlalchemy.exc
from flask import Blueprint, request, jsonify

import database.user
from utils.token import JWT
from utils import rabbitmq
from .error import exception


blueprint = Blueprint('user', __name__, url_prefix='/user')


@blueprint.route("/add", methods=["POST"])
def add():
    token = JWT.from_request_header(request)

    if not token.is_admin:
        raise exception.NotEnoughPrivilege()

    json = request.get_json()
    username = json.get('username')
    password = json.get('password')
    scope = json.get('scope')

    if username is None or password is None or scope is None:
        raise exception.InvalidRequest()

    if '/' in username:
        raise exception.UsernameNotValid()

    if not JWT.scope_is_valid(scope):
        raise exception.ScopeNotValid()

    try:
        update_rabbitmq_user(username, password)
        user = database.user.add(username, password, scope)
        return jsonify(user)
    except sqlalchemy.exc.IntegrityError:
        raise exception.UserAlreadyExists()


@blueprint.route("/list", methods=["GET"])
def list_all():
    token = JWT.from_request_header(request)

    if not token.is_admin:
        raise exception.NotEnoughPrivilege()

    limit = request.args.get('limit', 10)
    offset = request.args.get('limit', 0)

    users = database.user.get_all(limit, offset)
    return jsonify({
        'limit': limit,
        'offset': offset,
        'users': users
    })


@blueprint.route("/<string:username>", methods=["GET", "PUT", "DELETE"])
def detail(username):
    token = JWT.from_request_header(request)
    username = token.username if username is None else username

    if not token.is_admin and username != token.username:
        raise exception.NotEnoughPrivilege()

    user = database.user.get(username)
    if user is None:
        raise exception.UserDoesNotExist()

    if request.method == "GET":
        return jsonify(user)
    elif request.method == "PUT":
        new_password = request.get_json().get('password')
        new_scope = request.get_json().get('scope')

        if new_password is None and new_scope is None:
            raise exception.InvalidRequest()

        if new_password is not None:
            update_rabbitmq_user(username, new_password)
            user = database.user.change_password(username, new_password)
            return jsonify(user)
        if new_scope is not None:
            if not JWT.scope_is_valid(new_scope):
                raise exception.ScopeNotValid()
            # TODO: = currently it is not possible to change scope of rabbitmq without providing a new set of password
            user = database.user.change_scope(username, new_scope)
            return jsonify(user)
    elif request.method == "DELETE":
        delete_rabbitmq_user(username)
        database.user.delete_user(username)
        return jsonify(), 204


def update_rabbitmq_user(username: str, password: str):
    try:
        scope = 'administrator' if username == 'admin' else 'worker'
        status_code = rabbitmq.put_user(username, password, scope)
        if status_code != 201 and status_code != 204:
            raise exception.RabbitMQPutUserFailed(status_code)

        if scope == 'administrator':
            status_code = rabbitmq.put_permission('zimfarm', username)
        else:
            status_code = rabbitmq.put_permission('zimfarm', username, write='')
        if status_code != 201 and status_code != 204:
            raise exception.RabbitMQPutPermissionFailed(status_code)
    except urllib.error.HTTPError as error:
        code = error.getcode()
        raise exception.RabbitMQError(code)

def delete_rabbitmq_user(username: str):
    try:
        status_code = rabbitmq.delete_user(username)
        if status_code != 204:
            raise exception.RabbitMQDeleteUserFailed(status_code)
    except urllib.error.HTTPError as error:
        code = error.getcode()
        raise exception.RabbitMQError(code)