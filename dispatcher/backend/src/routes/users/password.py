from typing import Union

import jsonschema
import paramiko
from bson import ObjectId
from flask import request, jsonify, Response

from routes import authenticate, authenticate2, bson_object_id, url_object_id, errors
from utils.token import AccessToken
from utils.mongo import Users


@authenticate2
@url_object_id(['user'])
def change(token: AccessToken.Payload, user: Union[ObjectId, str]):
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