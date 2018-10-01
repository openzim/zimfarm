from typing import Union

from bson import ObjectId
from flask import request, jsonify
from jsonschema import validate, ValidationError
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash

from routes import authenticate2, url_object_id, errors
from utils.mongo import Users
from utils.token import AccessToken


@authenticate2
def list(token: AccessToken.Payload):
    # check user permission
    if not token.get_permission('users', 'read'):
        raise errors.NotEnoughPrivilege()

    # unpack url parameters
    skip = request.args.get('skip', default=0, type=int)
    limit = request.args.get('limit', default=20, type=int)
    skip = 0 if skip < 0 else skip
    limit = 20 if limit <= 0 else limit

    # get users from database
    cursor = Users().find({}, {'_id': 1, 'username': 1, 'email': 1})
    users = [user for user in cursor]

    return jsonify({
        'meta': {
            'skip': skip,
            'limit': limit,
        },
        'items': users
    })


@authenticate2
def create(token: AccessToken.Payload):
    # check user permission
    if not token.get_permission('users', 'create'):
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

    try:
        user_id = Users().insert_one(request_json).inserted_id
        return jsonify({'_id': user_id})
    except DuplicateKeyError:
        raise errors.BadRequest('User already exists')

@authenticate2
@url_object_id('user')
def get(token: AccessToken.Payload, user: Union[ObjectId, str]):
    # check user permission
    if user != token.user_id and user != token.username:
        if not token.get_permission('users', 'read'):
            raise errors.NotEnoughPrivilege()

    # find user based on _id or username
    user = Users().find_one({'$or': [{'_id': user}, {'username': user}]},
                            {'_id': 1, 'username': 1, 'email': 1})

    if user is None:
        raise errors.NotFound()
    return jsonify(user)