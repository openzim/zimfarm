import base64
import pathlib
import logging
import tempfile
import datetime
import binascii
import subprocess
from uuid import uuid4

from flask import request, jsonify

from routes import errors
from common.constants import (
    OPENSSL_BIN,
    MESSAGE_VALIDITY,
    REFRESH_TOKEN_EXPIRY,
    TOKEN_EXPIRY,
)
from common import getnow
from common.mongo import Users, RefreshTokens
from utils.token import AccessToken

logger = logging.getLogger(__name__)


def asymmetric_key_auth():
    """ authenticate using signed message and generate tokens

        - message in X-SSHAuth-Message HTTP header
        - base64 signature in X-SSHAuth-Signature HTTP header
        - decode standard message: username:timestamp(UTC ISO)
        - verify timestamp is less than a minute old
        - verify username matches our database
        - verify signature of message with username's public keys
        - generate tokens"""

    # check the message's validity
    try:
        message = request.headers["X-SSHAuth-Message"]
        signature = base64.b64decode(request.headers["X-SSHAuth-Signature"])
        username, timestamp = message.split(":", 1)
        timestamp = datetime.datetime.fromisoformat(timestamp)
    except KeyError as exc:
        raise errors.BadRequest("Missing header for `{}`".format("".join(exc.args[:1])))
    except binascii.Error:
        raise errors.BadRequest("Invalid signature format (not base64)")
    except Exception as exc:
        logger.error(f"Invalid message format: {exc}")
        logger.exception(exc)
        raise errors.BadRequest("Invalid message format")

    if (datetime.datetime.utcnow() - timestamp).total_seconds() > MESSAGE_VALIDITY:
        raise errors.Unauthorized(
            f"message too old or peers desyncrhonised: {MESSAGE_VALIDITY}s"
        )

    user = Users().find_one(
        {"username": username}, {"username": 1, "scope": 1, "ssh_keys": 1}
    )
    if user is None:
        raise errors.Unauthorized("User not found")  # we shall never get there

    ssh_keys = user.pop("ssh_keys", [])

    # check that the message was signed with a known private key
    authenticated = False
    with tempfile.TemporaryDirectory() as tmp_dirname:
        tmp_dir = pathlib.Path(tmp_dirname)
        message_path = tmp_dir.joinpath("message")
        signatured_path = tmp_dir.joinpath(f"{message_path.name}.sig")

        with open(message_path, "w", encoding="ASCII") as fp:
            fp.write(message)

        with open(signatured_path, "wb") as fp:
            fp.write(signature)

        for ssh_key in ssh_keys:
            pkcs8_data = ssh_key.get("pkcs8_key")
            if not pkcs8_data:  # User record has no PKCS8 version
                continue

            pkcs8_key = tmp_dir.joinpath("pubkey")
            with open(pkcs8_key, "w") as fp:
                fp.write(pkcs8_data)

            pkey_util = subprocess.run(
                [
                    OPENSSL_BIN,
                    "pkeyutl",
                    "-verify",
                    "-pubin",
                    "-inkey",
                    str(pkcs8_key),
                    "-in",
                    str(message_path),
                    "-sigfile",
                    signatured_path,
                ],
                capture_output=True,
                text=True,
            )
            if pkey_util.returncode == 0:  # signature verified
                authenticated = True
                break
    if not authenticated:
        raise errors.Unauthorized("Could not find matching key for signature")

    # we're now authenticated ; generate tokens
    access_token = AccessToken.encode(user)
    refresh_token = uuid4()

    # store refresh token in database
    RefreshTokens().insert_one(
        {
            "token": refresh_token,
            "user_id": user["_id"],
            "expire_time": getnow() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRY),
        }
    )

    # send response
    response_json = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": datetime.timedelta(hours=TOKEN_EXPIRY).total_seconds(),
        "refresh_token": refresh_token,
    }
    response = jsonify(response_json)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response
