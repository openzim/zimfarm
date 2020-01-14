import base64
import binascii
from datetime import datetime
from http import HTTPStatus

import paramiko
from flask import request, Response
from marshmallow import Schema, fields, validate, ValidationError

from routes import errors
from common.mongo import Users


def ssh_key():
    """
    Validate ssh public keys exists and matches with username
    """

    # validate request json
    class KeySchema(Schema):
        username = fields.String(required=True, validate=validate.Length(min=1))
        key = fields.String(required=True, validate=validate.Length(min=1))

    try:
        request_json = KeySchema().load(request.get_json())
    except ValidationError as e:
        raise errors.InvalidRequestJSON(e.messages)

    # compute fingerprint
    try:
        key = request_json["key"]
        rsa_key = paramiko.RSAKey(data=base64.b64decode(key))
        fingerprint = binascii.hexlify(rsa_key.get_fingerprint()).decode()
    except (binascii.Error, paramiko.SSHException):
        raise errors.BadRequest("Invalid RSA key")

    # database
    username = request_json["username"]
    user = Users().update_one(
        {
            "username": username,
            "ssh_keys": {"$elemMatch": {"fingerprint": fingerprint}},
        },
        {"$set": {"ssh_keys.$.last_used": datetime.now()}},
    )

    if user.matched_count == 0:
        raise errors.Unauthorized()
    return Response(status=HTTPStatus.NO_CONTENT)
