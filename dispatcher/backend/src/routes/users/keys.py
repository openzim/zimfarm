import base64
import binascii
import os
import subprocess
import tempfile
from http import HTTPStatus

import paramiko
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import Response, jsonify, request
from marshmallow import ValidationError

import common.schemas.orms as cso
import db.models as dbm
import errors.http as http_errors
from common.schemas.parameters import KeySchema
from db import dbsession
from routes import authenticate, errors
from routes.base import BaseRoute
from utils.check import raise_if_none
from utils.token import AccessToken


class KeysRoute(BaseRoute):
    rule = "/<string:username>/keys"
    name = "keys"
    methods = ["GET", "POST"]

    @authenticate
    @dbsession
    def get(self, username: str, token: AccessToken.Payload, session: so.Session):
        # if user in url is not user in token, check user permission
        if username != token.username:
            if not token.get_permission("users", "ssh_keys"):
                raise errors.NotEnoughPrivilege()

        # find user based on username
        orm_user = dbm.User.get(session, username, errors.NotFound, fetch_ssh_keys=True)
        return jsonify(list(map(cso.SshKeyRead().dump, orm_user.ssh_keys)))

    @authenticate
    @dbsession
    def post(self, username: str, token: AccessToken.Payload, session: so.Session):
        # if user in url is not user in token, not allowed to add ssh keys
        if username != token.username:
            if not token.get_permission("users", "ssh_keys"):
                raise errors.NotEnoughPrivilege()

        try:
            request_json = KeySchema().load(request.get_json())
        except ValidationError as e:
            raise http_errors.InvalidRequestJSON(e.messages)

        # parse public key string
        key = request_json["key"]
        key_parts = key.split(" ")
        if len(key_parts) >= 2:
            key = key_parts[1]

        # compute fingerprint
        try:
            rsa_key = paramiko.RSAKey(data=base64.b64decode(key))
            fingerprint = binascii.hexlify(rsa_key.get_fingerprint()).decode()
        except (binascii.Error, paramiko.SSHException):
            raise errors.BadRequest("Invalid RSA key")

        # find out if user exist
        current_user = dbm.User.get(
            session, username, errors.NotFound, "User not found"
        )

        # find out if new ssh already exist
        orm_ssh_key = session.execute(
            sa.select(dbm.Sshkey)
            .where(dbm.Sshkey.user_id == current_user.id)
            .where(dbm.Sshkey.fingerprint == fingerprint)
        ).scalar_one_or_none()

        if orm_ssh_key:
            raise errors.BadRequest("SSH key already exists")

        # get PKCS8 - ssh-keygen -e -f xxx.priv -m PKCS8
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pub", delete=False) as fp:
            fp.write("ssh-rsa {} {}\n".format(key, request_json["name"]))
        keygen = subprocess.run(
            ["/usr/bin/ssh-keygen", "-e", "-f", fp.name, "-m", "PKCS8"],
            capture_output=True,
            text=True,
        )
        if keygen.returncode != 0:
            raise errors.BadRequest(keygen.stderr)
        pkcs8_key = keygen.stdout
        os.unlink(fp.name)

        # add new ssh key to database
        ssh_key = dbm.Sshkey(
            mongo_val=None,
            name=request_json["name"],
            fingerprint=fingerprint,
            key=key,
            type="RSA",
            added=sa.func.current_timestamp(),
            last_used=None,
            pkcs8_key=pkcs8_key,
        )
        ssh_key.user_id = current_user.id

        session.add(ssh_key)

        return Response(status=HTTPStatus.CREATED)


class KeyRoute(BaseRoute):
    rule = "/<string:username>/keys/<string:fingerprint>"
    name = "key"
    methods = ["GET", "DELETE"]

    @dbsession
    def get(self, username: str, fingerprint: str, session: so.Session):
        # list of permission to test the matching user against
        requested_permissions = request.args.getlist("with_permission") or []

        stmt = (
            sa.select(
                dbm.Sshkey.type,
                dbm.Sshkey.name,
                dbm.Sshkey.key,
                dbm.User.username,
                dbm.User.scope,
                dbm.User.deleted,
            )
            .join_from(dbm.Sshkey, dbm.User)
            .where(dbm.Sshkey.fingerprint == fingerprint)
        )
        if username != "-":
            stmt = stmt.where(dbm.User.username == username)

        user_with_key = session.execute(stmt).fetchone()

        # no user means no matching SSH key for fingerprint
        dbm.User.check(user_with_key, errors.NotFound)

        for permission in requested_permissions:
            namespace, perm_name = permission.split(".", 1)
            if not user_with_key.scope.get(namespace, {}).get(perm_name):
                raise errors.NotEnoughPrivilege(permission)

        payload = {
            "username": user_with_key.username,
            "key": user_with_key.key,
            "type": user_with_key.type,
            "name": user_with_key.name,
        }

        return jsonify(payload)

    @authenticate
    @dbsession
    def delete(
        self,
        username: str,
        fingerprint: str,
        token: AccessToken.Payload,
        session: so.Session,
    ):
        # if user in url is not user in token, check user permission
        if username != token.username:
            if not token.get_permission("users", "ssh_keys"):
                raise errors.NotEnoughPrivilege()

        # find out if user exist
        current_user = dbm.User.get(
            session, username, errors.NotFound, "User not found"
        )

        orm_ssh_key = session.execute(
            sa.delete(dbm.Sshkey)
            .where(dbm.Sshkey.user_id == current_user.id)
            .where(dbm.Sshkey.fingerprint == fingerprint)
            .returning(dbm.Sshkey.id)
        ).scalar_one_or_none()
        raise_if_none(orm_ssh_key, errors.NotFound, "No SSH key with this fingerprint")

        return Response(status=HTTPStatus.NO_CONTENT)
