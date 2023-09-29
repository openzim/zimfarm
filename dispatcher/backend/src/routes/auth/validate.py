import base64
import binascii
from http import HTTPStatus

import paramiko
import paramiko.pkey
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import Response, request
from marshmallow import Schema, ValidationError, fields, validate

import db.models as dbm
import errors.http as http_errors
from common import getnow
from routes import errors
from utils.check import raise_if_none
from db import dbsession

@dbsession
def ssh_key(session: so.Session):
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
        raise http_errors.InvalidRequestJSON(e.messages)

    # compute fingerprint
    try:
        key = request_json["key"]
        print(key)
        print(base64.b64decode(key))
        rsa_key = paramiko.RSAKey(data=base64.b64decode(key))
        # rsa_key = paramiko.pkey.PublicBlob(type_ = "RSA", blob=base64.b64decode(key))
        # print(rsa_key.)
        fingerprint = binascii.hexlify(rsa_key.get_fingerprint()).decode()
    except (binascii.Error, paramiko.SSHException) as exc:
        print(exc)
        raise errors.BadRequest("Invalid RSA key")

    # database
    username = request_json["username"]
    orm_ssh_key = session.execute(
        sa.select(dbm.Sshkey)
        .join(dbm.User)
        .where(dbm.User.username == username)
        .where(dbm.Sshkey.fingerprint == fingerprint)
    ).scalar_one_or_none()
    raise_if_none(orm_ssh_key, errors.Unauthorized)
    dbm.User.check(orm_ssh_key.user, errors.Unauthorized)
    orm_ssh_key.last_used = getnow()
    return Response(status=HTTPStatus.NO_CONTENT)
