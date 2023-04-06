import base64
import binascii
from http import HTTPStatus

import paramiko
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import Response, request
from marshmallow import Schema, ValidationError, fields, validate

import db.models as dbm
from common import getnow
from db.engine import Session
from routes import errors


def ssh_key():
    """
    Validate ssh public keys exists and matches with username
    """
    with Session.begin() as session:
        res = _ssh_key_inner(session)
    return res


def _ssh_key_inner(session: so.Session):
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
    orm_ssh_key = session.execute(
        sa.select(dbm.Sshkey)
        .join(dbm.User)
        .where(dbm.User.username == username)
        .where(dbm.Sshkey.fingerprint == fingerprint)
    ).scalar_one_or_none()
    if orm_ssh_key is None:
        raise errors.Unauthorized()
    orm_ssh_key.last_used = getnow()
    return Response(status=HTTPStatus.NO_CONTENT)
