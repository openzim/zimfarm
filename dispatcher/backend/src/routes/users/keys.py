import base64
import binascii
from datetime import datetime
from typing import Union

import jsonschema
import paramiko
from bson import ObjectId
from flask import request, jsonify, Response

from routes import authenticate2, url_object_id, errors
from utils.mongo import Users
from utils.token import AccessToken


@authenticate2
@url_object_id('user')
def list(token: AccessToken.Payload, user: Union[ObjectId, str]):
    # if user in url is not user in token, check user permission
    if user != token.user_id and user != token.username:
        if not token.get_permission('users', 'ssh_keys.read'):
            raise errors.NotEnoughPrivilege()

    user = Users().find_one({'$or': [{'_id': user}, {'username': user}]}, {'ssh_keys': 1})
    if user is None:
        raise errors.NotFound()

    ssh_keys = user.get('ssh_keys', [])
    return jsonify(ssh_keys)


@authenticate2
@url_object_id(['user'])
def add(token: AccessToken.Payload, user: Union[ObjectId, str]):
    # if user in url is not user in token, not allowed to add ssh keys
    if user != token.user_id and user != token.username:
        raise errors.NotEnoughPrivilege()

    # validate request json
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "key": {"type": "string", "minLength": 1}
        },
        "required": ["name", "key"],
        "additionalProperties": False
    }
    try:
        request_json = request.get_json()
        jsonschema.validate(request_json, schema)
    except jsonschema.ValidationError as error:
        raise errors.BadRequest(error.message)

    # parse public key string
    key = request_json['key']
    key_parts = key.split(' ')
    if len(key_parts) >= 2:
        key = key_parts[1]

    # compute fingerprint
    try:
        rsa_key = paramiko.RSAKey(data=base64.b64decode(key))
        fingerprint = binascii.hexlify(rsa_key.get_fingerprint()).decode()
    except (binascii.Error, paramiko.SSHException):
        raise errors.BadRequest('Invalid RSA key')

    # database
    path = 'ssh_keys.{}'.format(fingerprint)
    filter = {'$or': [{'_id': user, 'path': {'$exists': False}},
                      {'username': user}]}
    user_id = Users().update_one(filter, {'$set': {path: {
        'name': request_json['name'],
        'key': key,
        'type': 'RSA',
        'added': datetime.now(),
        'last_used': None
    }}}).upserted_id

    if user_id is not None:
        return jsonify()
    else:
        raise errors.BadRequest('Key already exists')


@authenticate2
@url_object_id('user')
def delete(token: AccessToken.Payload, user: Union[ObjectId, str], fingerprint: str):
    # if user in url is not user in token, check user permission
    if user != token.user_id and user != token.username:
        if not token.get_permission('users', 'ssh_keys.delete'):
            raise errors.NotEnoughPrivilege()

    # database
    path = 'ssh_keys.{}'.format(fingerprint)
    modified_count = Users().update_one({'$or': [{'_id': user}, {'username': user}]},
                                        {'$unset': {path: ''}}).modified_count

    if modified_count > 0:
        return Response()
    else:
        raise errors.NotFound()
