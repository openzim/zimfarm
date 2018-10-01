import base64
import binascii
from datetime import datetime
from typing import Union

import jsonschema
import paramiko
from bson import ObjectId
from flask import request, jsonify, Response

from routes import authenticate, authenticate2, bson_object_id, url_object_id, errors
from utils.mongo import Users
from utils.token import AccessToken


@authenticate
@bson_object_id(['user_id'])
def list(user_id: ObjectId, user: dict):
    # TODO: check permission
    ssh_keys = Users().find_one({'_id': user_id}, {'ssh_keys': 1}).get('ssh_keys', [])
    return jsonify(ssh_keys)


@authenticate2
@url_object_id(['user'])
def add(token: AccessToken.Payload, user: Union[ObjectId, str]):
    # TODO: change user_id to user in request

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

    # parse key
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
    if isinstance(user, ObjectId):
        filter = {'_id': user}
    else:
        filter = {'username': user}
    path = 'ssh_keys.{}'.format(fingerprint)
    filter[path] = {'$exists': False}

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
