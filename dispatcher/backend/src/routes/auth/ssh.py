import os
import base64
import pathlib
import logging
import tempfile
import datetime
import subprocess
from uuid import uuid4

import jsonschema
from flask import request, jsonify

from routes import errors
from common.mongo import Users, RefreshTokens
from utils.token import AccessToken

OPENSSL_BIN = os.getenv("OPENSSL_BIN", "/usr/bin/openssl")

logger = logging.getLogger(__name__)


def asymmetric_key_auth():
    """ authenticate using signed message and generate tokens

        - decode standard message: username:timestamp
        - verify signature of message with username's public keys
        - generate tokens if OK """

    schema = {
        "type": "object",
        "properties": {
            "username": {"type": "string", "minLength": 1},
            "payload": {"type": "string", "minLength": 1},
            "signed_payload": {"type": "string", "minLength": 1},
        },
        "required": ["username", "payload", "signed_payload"],
        "additionalProperties": False,
    }
    try:
        request_json = request.get_json()
        jsonschema.validate(request_json, schema)
    except jsonschema.ValidationError as error:
        raise errors.BadRequest(error.message)

    user = Users().find_one({"username": request_json["username"]})
    if user is None:
        raise errors.Unauthorized()  # we shall never get there

    with tempfile.TemporaryDirectory() as tmp_dirname:
        tmp_dir = pathlib.Path(tmp_dirname)
        payload_path = tmp_dir.joinpath("payload.txt")
        signatured_path = tmp_dir.joinpath(f"{payload_path.name}.sig")

        with open(payload_path, "w", encoding="utf-8") as fp:
            fp.write(request_json["payload"])

        with open(signatured_path, "wb") as fp:
            fp.write(base64.b64decode(request_json["signed_payload"]))

        for ssh_key in user.get("ssh_keys", []):
            if not ssh_key.get("pkcs8"):
                continue
            pkcs8_key = tmp_dir.joinpath("pubkey")
            with open(pkcs8_key, "w") as fp:
                fp.write(ssh_key.get("pkcs8"))

            pkey_util = subprocess.run(
                [
                    "OPENSSL_BIN",
                    "pkeyutl",
                    "-verify",
                    "-pubin",
                    "-inkey",
                    str(pkcs8_key),
                    "-in",
                    str(payload_path),
                    "-sigfile",
                    signatured_path,
                ]
            )
            if pkey_util.returncode != 0:
                logger.debug(f"{pkey_util.returncode} {pkey_util.stderr}")
                raise errors.Unauthorized()

    # we're now authenticated ; generate tokens
    access_token = AccessToken.encode(user)
    refresh_token = uuid4()

    # store refresh token in database
    RefreshTokens().insert_one(
        {
            "token": refresh_token,
            "user_id": user["_id"],
            "expire_time": datetime.datetime.now() + datetime.timedelta(days=30),
        }
    )

    # send response
    response_json = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": datetime.timedelta(minutes=60).total_seconds(),
        "refresh_token": refresh_token,
    }
    response = jsonify(response_json)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response
