import base64
import binascii

import paramiko
import jsonschema
from flask import request, Response

from routes import errors
from utils.mongo import Users


def ssh_key():
    """
    Validate ssh public keys exists and matches with username
    """

    # validate request json
    schema = {
        "type": "object",
        "properties": {
            "username": {"type": "string", "minLength": 1},
            "key": {"type": "string", "minLength": 1}
        },
        "required": ["username", "key"],
        "additionalProperties": False
    }
    try:
        request_json = request.get_json()
        jsonschema.validate(request_json, schema)
    except jsonschema.ValidationError as error:
        raise errors.BadRequest(error.message)

    # compute fingerprint
    try:
        key = request_json['key']
        rsa_key = paramiko.RSAKey(data=base64.b64decode(key))
        fingerprint = binascii.hexlify(rsa_key.get_fingerprint()).decode()
    except (binascii.Error, paramiko.SSHException):
        raise errors.BadRequest('Invalid RSA key')

    # database
    username = request_json['username']
    user = Users().find_one({'username': username,
                             'ssh_keys': {'$elemMatch': {'fingerprint': fingerprint}}})

    if user is None:
        raise errors.Unauthorized()
    else:
        return Response()
