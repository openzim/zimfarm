import base64
import binascii
import datetime
import logging
import pathlib
import subprocess
import tempfile

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import jsonify, request

import db.models as dbm
from common.constants import MESSAGE_VALIDITY, OPENSSL_BIN, TOKEN_EXPIRY
from db import dbsession
from routes import errors
from routes.auth.oauth2 import OAuth2
from routes.utils import raise_if, raise_if_none
from utils.token import AccessToken

logger = logging.getLogger(__name__)


@dbsession
def asymmetric_key_auth(session: so.Session):
    """authenticate using signed message and generate tokens

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

    orm_user = session.execute(
        sa.select(dbm.User)
        .where(dbm.User.username == username)
        .options(so.selectinload(dbm.User.ssh_keys))
    ).scalar_one_or_none()
    raise_if_none(
        orm_user, errors.Unauthorized("User not found")
    )  # we shall never get there

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

        for ssh_key in orm_user.ssh_keys:
            pkcs8_data = ssh_key.pkcs8_key
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
    raise_if(
        not authenticated,
        errors.Unauthorized("Could not find matching key for signature"),
    )

    # we're now authenticated ; generate access token
    access_token = AccessToken.encode_db(orm_user)

    # genereate + store refresh token in database
    refresh_token = OAuth2.generate_refresh_token(orm_user.id, session)

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
