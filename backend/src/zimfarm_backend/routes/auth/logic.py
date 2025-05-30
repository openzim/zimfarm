import base64
import binascii
import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session as OrmSession
from werkzeug.security import check_password_hash

from zimfarm_backend import logger
from zimfarm_backend.common import constants
from zimfarm_backend.db import gen_dbsession
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.refresh_token import (
    create_refresh_token,
    delete_refresh_token,
    expire_refresh_tokens,
    get_refresh_token,
)
from zimfarm_backend.db.user import get_user_by_username
from zimfarm_backend.exceptions import PEMPublicKeyLoadError
from zimfarm_backend.routes.auth.models import CredentialsIn, Token
from zimfarm_backend.routes.http_errors import (
    BadRequestError,
    ForbiddenError,
    UnauthorizedError,
)
from zimfarm_backend.utils.token import generate_access_token, verify_signed_message

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/authorize")
def auth_with_credentials(
    credentials: CredentialsIn,
    response: Response,
    db_session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> Token:
    """Authorize a user with username and password."""
    try:
        db_user = get_user_by_username(db_session, username=credentials.username)
    except RecordDoesNotExistError as exc:
        raise UnauthorizedError() from exc

    if not (
        db_user.password_hash
        and check_password_hash(db_user.password_hash, credentials.password)
    ):
        raise UnauthorizedError("Invalid credentials")

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"

    return Token(
        access_token=generate_access_token(str(db_user.id)),
        refresh_token=str(
            create_refresh_token(session=db_session, user_id=db_user.id).token
        ),
        expires_in=constants.JWT_TOKEN_EXPIRY_DURATION,
    )


@router.post("/refresh")
def refresh_access_token(
    refresh_token: Annotated[UUID, Header(description="Old refresh token")],
    db_session: Annotated[OrmSession, Depends(gen_dbsession)],
    response: Response,
) -> Token:
    """Issue a new set of access and refresh token after validating old refresh token.

    Old refresh token can only be used once and hence is removed from database
    Unused but expired refresh token is also deleted from database.
    """
    try:
        db_refresh_token = get_refresh_token(db_session, token=refresh_token)
    except RecordDoesNotExistError as exc:
        raise UnauthorizedError() from exc

    now = datetime.datetime.now(datetime.UTC)
    if db_refresh_token.expire_time < now:
        raise UnauthorizedError("Refresh token expired")

    delete_refresh_token(db_session, token=refresh_token)
    expire_refresh_tokens(db_session, expire_time=now)

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"

    return Token(
        access_token=generate_access_token(str(db_refresh_token.user_id)),
        refresh_token=str(
            create_refresh_token(
                session=db_session, user_id=db_refresh_token.user_id
            ).token
        ),
        expires_in=constants.JWT_TOKEN_EXPIRY_DURATION,
    )


@router.post("/ssh-authorize")
def authenticate_user_with_ssh_keys(
    db_session: Annotated[OrmSession, Depends(gen_dbsession)],
    x_sshauth_message: Annotated[
        str,
        Header(description="message (format): username:timestamp (UTC ISO)"),
    ],
    x_sshauth_signature: Annotated[
        str, Header(description="signature, base64-encoded")
    ],
    response: Response,
) -> Token:
    """Authenticate using signed message and generate tokens."""
    try:
        signature = base64.standard_b64decode(x_sshauth_signature)
    except binascii.Error as exc:
        raise BadRequestError("Invalid signature format (not base64)") from exc

    try:
        # decode message: username:timestamp(UTC ISO)
        username, timestamp_str = x_sshauth_message.split(":", 1)
        timestamp = datetime.datetime.fromisoformat(timestamp_str)
    except ValueError as exc:
        raise BadRequestError("Invalid message format.") from exc

    # verify timestamp is less than MESSAGE_VALIDITY
    if (
        datetime.datetime.now(datetime.UTC) - timestamp
    ).total_seconds() > constants.MESSAGE_VALIDITY_DURATION:
        raise UnauthorizedError(
            "Difference betweeen message time and server time is "
            f"greater than {constants.MESSAGE_VALIDITY_DURATION}s"
        )

    # verify user with username exists in database
    try:
        db_user = get_user_by_username(
            db_session,
            username=username,
            fetch_ssh_keys=True,
        )
    except RecordDoesNotExistError as exc:
        raise UnauthorizedError() from exc

    # verify signature of message with user's public keys
    authenticated = False
    for ssh_key in db_user.ssh_keys:
        try:
            if verify_signed_message(
                bytes(ssh_key.pkcs8_key, encoding="ascii"),
                signature,
                bytes(x_sshauth_message, encoding="ascii"),
            ):
                authenticated = True
                break
        except PEMPublicKeyLoadError as exc:
            logger.exception("error while verifying message using public key")
            raise ForbiddenError("Unable to load public_key") from exc

    if not authenticated:
        raise UnauthorizedError("Could not find matching key for signature.")

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    # generate tokens
    return Token(
        access_token=generate_access_token(str(db_user.id)),
        refresh_token=str(
            create_refresh_token(session=db_session, user_id=db_user.id).token
        ),
        expires_in=constants.JWT_TOKEN_EXPIRY_DURATION,
    )
