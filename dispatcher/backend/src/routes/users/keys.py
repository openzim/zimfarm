import base64
import binascii
import os
import subprocess
import tempfile
from datetime import datetime
from http import HTTPStatus

import paramiko
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import Response, jsonify, request
from marshmallow import ValidationError

import common.schemas.orms as cso
import db.models as dbm
from common.schemas.parameters import KeySchema
from db.engine import Session
from routes import authenticate, errors, url_object_id
from routes.base import BaseRoute
from utils.token import AccessToken


class KeysRoute(BaseRoute):
    rule = "/<string:username>/keys"
    name = "keys"
    methods = ["GET", "POST"]

    @authenticate
    @url_object_id("username")
    def get(self, username: str, token: AccessToken.Payload):
        # if user in url is not user in token, check user permission
        if username != token.username:
            if not token.get_permission("users", "ssh_keys"):
                raise errors.NotEnoughPrivilege()

        # find user based on username
        with Session.begin() as session:
            orm_user = session.execute(
                sa.select(dbm.User)
                .where(dbm.User.username == username)
                .options(so.selectinload(dbm.User.ssh_keys))
            ).scalar_one_or_none()

            if orm_user is None:
                raise errors.NotFound()

            api_ssh_keys = list(map(cso.SshKeyRead().dump, orm_user.ssh_keys))

        return jsonify(api_ssh_keys)

    @authenticate
    @url_object_id(["username"])
    def post(self, username: str, token: AccessToken.Payload):
        # if user in url is not user in token, not allowed to add ssh keys
        if username != token.username:
            if not token.get_permission("users", "ssh_keys"):
                raise errors.NotEnoughPrivilege()

        try:
            request_json = KeySchema().load(request.get_json())
        except ValidationError as e:
            raise errors.InvalidRequestJSON(e.messages)

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

        with Session.begin() as session:
            # find out if user exist
            current_user_id = session.execute(
                sa.select(dbm.User.id).where(dbm.User.username == username)
            ).scalar_one_or_none()

            if not current_user_id:
                raise errors.NotFound("User not found")

            # find out if new ssh already exist
            orm_ssh_key = session.execute(
                sa.select(dbm.Sshkey)
                .where(dbm.Sshkey.user_id == current_user_id)
                .where(dbm.Sshkey.fingerprint == fingerprint)
            ).scalar_one_or_none()

            if orm_ssh_key:
                raise errors.BadRequest("SSH key already exists")

            # get PKCS8 - ssh-keygen -e -f xxx.priv -m PKCS8
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".pub", delete=False
            ) as fp:
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
            ssh_key.user_id = current_user_id

            session.add(ssh_key)

        return Response(status=HTTPStatus.CREATED)


class KeyRoute(BaseRoute):
    rule = "/<string:username>/keys/<string:fingerprint>"
    name = "key"
    methods = ["GET", "DELETE"]

    @url_object_id("username")
    @url_object_id("fingerprint")
    def get(self, username: str, fingerprint: str):
        # list of permission to test the matching user against
        requested_permissions = request.args.getlist("with_permission") or []

        with Session.begin() as session:
            stmt = (
                sa.select(
                    dbm.Sshkey.type,
                    dbm.Sshkey.name,
                    dbm.Sshkey.key,
                    dbm.User.username,
                    dbm.User.scope,
                )
                .join_from(dbm.Sshkey, dbm.User)
                .where(dbm.Sshkey.fingerprint == fingerprint)
            )
            if username != "-":
                stmt = stmt.where(dbm.User.username == username)

            data = session.execute(stmt).fetchone()

            # no user means no matching SSH key for fingerprint
            if not data:
                raise errors.NotFound()

            for permission in requested_permissions:
                namespace, perm_name = permission.split(".", 1)
                if not data.scope.get(namespace, {}).get(perm_name):
                    raise errors.NotEnoughPrivilege(permission)

            payload = {
                "username": data.username,
                "key": data.key,
                "type": data.type,
                "name": data.name,
            }

        return jsonify(payload)

    @authenticate
    @url_object_id("username")
    @url_object_id("fingerprint")
    def delete(self, username: str, fingerprint: str, token: AccessToken.Payload):
        # if user in url is not user in token, check user permission
        if username != token.username:
            if not token.get_permission("users", "ssh_keys"):
                raise errors.NotEnoughPrivilege()

        with Session.begin() as session:
            # find out if user exist
            current_user_id = session.execute(
                sa.select(dbm.User.id).where(dbm.User.username == username)
            ).scalar_one_or_none()

            if not current_user_id:
                raise errors.NotFound("User not found")

            orm_ssh_key = session.execute(
                sa.delete(dbm.Sshkey)
                .where(dbm.Sshkey.user_id == current_user_id)
                .where(dbm.Sshkey.fingerprint == fingerprint)
                .returning(dbm.Sshkey.id)
            ).scalar_one_or_none()
            if orm_ssh_key is None:
                raise errors.NotFound("No SSH key with this fingerprint")

        return Response(status=HTTPStatus.NO_CONTENT)
