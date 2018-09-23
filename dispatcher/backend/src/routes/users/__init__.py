import base64
import binascii
from datetime import datetime

import paramiko
from bson import ObjectId
from flask import Blueprint, request, jsonify, Response
from jsonschema import validate, ValidationError
from werkzeug.security import check_password_hash, generate_password_hash

from . import keys
from .. import authenticate, bson_object_id, errors
from utils.mongo import Users


blueprint = Blueprint('user', __name__, url_prefix='/api/users')


@blueprint.route("/", methods=["GET", "POST"])
@authenticate
def collection(user: dict):
    """
    List or create users
    """

    if request.method == "GET":
        # check user permission
        if not user.get('scope', {}).get('users', {}).get('read', False):
            raise errors.NotEnoughPrivilege()

        # unpack url parameters
        skip = request.args.get('skip', default=0, type=int)
        limit = request.args.get('limit', default=20, type=int)
        skip = 0 if skip < 0 else skip
        limit = 20 if limit <= 0 else limit

        # get users from database
        cursor = Users().find({}, {'password_hash': 0})
        users = [user for user in cursor]

        return jsonify({
            'meta': {
                'skip': skip,
                'limit': limit,
            },
            'items': users
        })
    elif request.method == "POST":
        # check user permission
        if not user.get('scope', {}).get('users', {}).get('create', False):
            raise errors.NotEnoughPrivilege()

        # validate request json
        schema = {
            "type": "object",
            "properties": {
                "username": {"type": "string", "minLength": 1},
                "password": {"type": "string", "minLength": 6},
                "email": {"type": ["string", "null"]},
                "scope": {"type": "object"}
            },
            "required": ["username", "password"],
            "additionalProperties": False
        }
        try:
            request_json = request.get_json()
            validate(request_json, schema)
        except ValidationError as error:
            raise errors.BadRequest(error.message)

        # generate password hash
        password = request_json.pop('password')
        request_json['password_hash'] = generate_password_hash(password)

        user_id = Users().insert_one(request_json).inserted_id
        return jsonify({'_id': user_id})


@blueprint.route("/<string:user_id>", methods=["GET", "DELETE"])
@authenticate
@bson_object_id(['user_id'])
def document(user_id: ObjectId, user: dict):
    if request.method == "GET":
        # check user permission when not querying current user
        if not user_id == ObjectId(user['_id']):
            if not user.get('scope', {}).get('users', {}).get('read', False):
                raise errors.NotEnoughPrivilege()

        user = Users().find_one({'_id': user_id}, {'password_hash': 0})
        if user is None:
            raise errors.NotFound()

        return jsonify(user)
    elif request.method == "DELETE":
        # check user permission when not deleting current user
        if not user_id == ObjectId(user['_id']):
            if not user.get('scope', {}).get('users', {}).get('delete', False):
                raise errors.NotEnoughPrivilege()

        deleted_count = Users().delete_one({'_id': user_id}).deleted_count
        if deleted_count == 0:
            raise errors.NotFound()

        return Response()


@blueprint.route("/<string:user_id>/password", methods=["PATCH"])
@authenticate
@bson_object_id(['user_id'])
def change_password(user_id: ObjectId, user: dict):
    # check user permission when not updating current user
    if user_id != ObjectId(user['_id']):
        if not user.get('scope', {}).get('users', {}).get('update', False):
            raise errors.NotEnoughPrivilege()

    request_json = request.get_json()

    # TODO: use json schema to validate
    password_old = request_json.get('old', None)
    password_new = request_json.get('new', None)
    if password_new is None or password_old is None:
        raise errors.BadRequest()

    user = Users().find_one({'_id': user_id}, {'password_hash': 1})
    if user is None:
        raise errors.NotFound()

    valid = check_password_hash(user['password_hash'], password_old)
    if not valid:
        raise errors.Unauthorized()

    Users().update_one({'_id': ObjectId(user_id)},
                       {'$set': {'password_hash': generate_password_hash(password_new)}})
    return Response()


blueprint.add_url_rule('/<string:user_id>/keys', 'list_ssh_keys', keys.list, methods=['GET'])
blueprint.add_url_rule('/<string:user_id>/keys', 'add_ssh_keys', keys.add, methods=['POST'])

# @blueprint.route("/<string:user_id>/keys", methods=["GET", "POST"])
# @authenticate
# @bson_object_id(['user_id'])
# def ssh_keys(user_id: ObjectId, user: dict):
#     if request.method == "GET":
#         ssh_keys = Users().find_one({'_id': user_id}, {'ssh_keys': 1}).get('ssh_keys', [])
#         return jsonify(ssh_keys)
#     elif request.method == "POST":
#         # check user_id in url is the same as user_id in access token
#         if user_id != ObjectId(user['_id']):
#             raise errors.Unauthorized("Cannot add ssh key to other user")
#
#         # validate request json
#         schema = {
#             "type": "object",
#             "properties": {
#                 "name": {"type": "string", "minLength": 1},
#                 "key": {"type": "string", "minLength": 1}
#             },
#             "required": ["name", "key"],
#             "additionalProperties": False
#         }
#         try:
#             request_json = request.get_json()
#             validate(request_json, schema)
#         except ValidationError as error:
#             raise errors.BadRequest(error.message)
#
#         # parse key
#         key = request_json['key']
#         key_parts = key.split(' ')
#         if len(key_parts) >= 2:
#             key = key_parts[1]
#
#         # compute fingerprint
#         try:
#             rsa_key = paramiko.RSAKey(data=base64.b64decode(key))
#             fingerprint = binascii.hexlify(rsa_key.get_fingerprint()).decode()
#         except (binascii.Error, paramiko.SSHException):
#             raise errors.BadRequest('Invalid RSA key')
#
#         document = {
#             'fingerprint': fingerprint,
#             'name': request_json['name'],
#             'key': key,
#             'added': datetime.now(),
#             'last_used': None
#         }
#
#         return jsonify(document)