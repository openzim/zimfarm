import os
import base64
import binascii
import tempfile
import subprocess
from http import HTTPStatus
from datetime import datetime

import jsonschema
import paramiko
from flask import request, jsonify, Response

from routes import authenticate2, url_object_id, errors
from common.mongo import Users
from utils.token import AccessToken


@authenticate2
@url_object_id("username")
def list(username: str, token: AccessToken.Payload):
    # if user in url is not user in token, check user permission
    if username != token.username:
        if not token.get_permission("users", "ssh_keys.read"):
            raise errors.NotEnoughPrivilege()

    user = Users().find_one({"username": username}, {"ssh_keys": 1})
    if user is None:
        raise errors.NotFound()

    ssh_keys = user.get("ssh_keys", [])
    return jsonify(ssh_keys)


@authenticate2
@url_object_id(["username"])
def add(token: AccessToken.Payload, username: str):
    # if user in url is not user in token, not allowed to add ssh keys
    if username != token.username:
        raise errors.NotEnoughPrivilege()

    # validate request json
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "key": {"type": "string", "minLength": 1},
        },
        "required": ["name", "key"],
        "additionalProperties": False,
    }
    try:
        request_json = request.get_json()
        jsonschema.validate(request_json, schema)
    except jsonschema.ValidationError as error:
        raise errors.BadRequest(error.message)

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

    # get existing ssh key fingerprints
    user = Users().find_one({"username": username}, {"ssh_keys.fingerprint": 1})
    if user is None:
        raise errors.NotFound()

    # find out if new ssh already exist
    fingerprints = set([ssh_key["fingerprint"] for ssh_key in user.get("ssh_keys", [])])
    if fingerprint in fingerprints:
        raise errors.BadRequest("SSH key already exists")

    # add new ssh key to database
    ssh_key = {
        "name": request_json["name"],
        "fingerprint": fingerprint,
        "key": key,
        "type": "RSA",
        "added": datetime.now(),
        "last_used": None,
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pub", delete=False) as fp:
        fp.write("ssh-rsa {} {}\n".format(ssh_key["key"], ssh_key["name"]))
    keygen = subprocess.run(
        ["/usr/bin/ssh-keygen", "-e", "-f", fp.name, "-m", "PKCS8"],
        capture_output=True,
        text=True,
    )
    if keygen.returncode != 0:
        raise errors.BadRequest(keygen.stderr)
    ssh_key.update({"pkcs8_key": keygen.stdout})
    os.unlink(fp.name)

    Users().update_one(filter, {"$push": {"ssh_keys": ssh_key}})

    return Response(status=HTTPStatus.CREATED)


@authenticate2
@url_object_id("username")
def delete(token: AccessToken.Payload, username: str, fingerprint: str):
    # if user in url is not user in token, check user permission
    if username != token.username:
        if not token.get_permission("users", "ssh_keys.delete"):
            raise errors.NotEnoughPrivilege()

    # database
    result = Users().update_one(
        {"username": username}, {"$pull": {"ssh_keys": {"fingerprint": fingerprint}}}
    )

    if result.modified_count > 0:
        Response(status=HTTPStatus.NO_CONTENT)
    else:
        raise errors.NotFound()
