import base64
import binascii
import datetime
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session as OrmSession
from werkzeug.security import check_password_hash

from zimfarm_backend import logger
from zimfarm_backend.api.constants import JWT_TOKEN_EXPIRY_DURATION
from zimfarm_backend.api.routes.auth.models import (
    CredentialsIn,
    OAuth2CredentialsWithPassword,
    OAuth2CredentialsWithRefreshToken,
    RefreshTokenIn,
    Token,
)
from zimfarm_backend.api.routes.dependencies import get_current_account
from zimfarm_backend.api.routes.http_errors import (
    BadRequestError,
    ForbiddenError,
    UnauthorizedError,
)
from zimfarm_backend.api.token import generate_access_token
from zimfarm_backend.common import constants, getnow
from zimfarm_backend.common.schemas.orms import AccountSchema
from zimfarm_backend.db import gen_dbsession
from zimfarm_backend.db.account import create_account_schema, get_account_by_username
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Account
from zimfarm_backend.db.refresh_token import (
    create_refresh_token,
    delete_refresh_token,
    expire_refresh_tokens,
    get_refresh_token,
)
from zimfarm_backend.exceptions import PublicKeyLoadError
from zimfarm_backend.utils.cryptography import verify_signed_message

router = APIRouter(prefix="/auth", tags=["auth"])


def _access_token_response(
    db_session: OrmSession, db_account: Account, response: Response
):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    issue_time = getnow()
    return Token(
        access_token=generate_access_token(
            account_id=str(db_account.id),
            issue_time=issue_time,
        ),
        refresh_token=str(
            create_refresh_token(session=db_session, account_id=db_account.id).token
        ),
        expires_time=issue_time + datetime.timedelta(seconds=JWT_TOKEN_EXPIRY_DURATION),
    )


def _auth_with_credentials(
    db_session: OrmSession, credentials: CredentialsIn, response: Response
):
    """Authorize an account with username and password."""
    try:
        db_account = get_account_by_username(db_session, username=credentials.username)
    except RecordDoesNotExistError as exc:
        raise UnauthorizedError() from exc

    if not (
        db_account.password_hash
        and check_password_hash(db_account.password_hash, credentials.password)
    ):
        raise UnauthorizedError("Invalid credentials")

    return _access_token_response(db_session, db_account, response)


def _refresh_access_token(
    db_session: OrmSession, refresh_token: UUID, response: Response
):
    """Issue a new set of access and refresh tokens."""
    try:
        db_refresh_token = get_refresh_token(db_session, token=refresh_token)
    except RecordDoesNotExistError as exc:
        raise UnauthorizedError() from exc

    now = getnow()
    if db_refresh_token.expire_time < now:
        raise UnauthorizedError("Refresh token expired")

    delete_refresh_token(db_session, token=refresh_token)
    expire_refresh_tokens(db_session, expire_time=now)

    return _access_token_response(db_session, db_refresh_token.account, response)


@router.post("/authorize")
def auth_with_credentials(
    credentials: CredentialsIn,
    response: Response,
    db_session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> Token:
    """Authorize an account with username and password."""
    return _auth_with_credentials(db_session, credentials, response)


@router.post("/refresh")
def refresh_access_token(
    request: RefreshTokenIn,
    db_session: Annotated[OrmSession, Depends(gen_dbsession)],
    response: Response,
) -> Token:
    return _refresh_access_token(db_session, request.refresh_token, response)


@router.post("/ssh-authorize")
def authenticate_account_with_ssh_keys(
    db_session: Annotated[OrmSession, Depends(gen_dbsession)],
    x_sshauth_message: Annotated[
        str,
        Header(description="message (format): username:timestamp (ISO)"),
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
        # decode message: username:timestamp(ISO)
        username, timestamp_str = x_sshauth_message.split(":", 1)
        timestamp = datetime.datetime.fromisoformat(timestamp_str)
    except ValueError as exc:
        raise BadRequestError("Invalid message format.") from exc

    # verify timestamp is less than MESSAGE_VALIDITY
    if (getnow() - timestamp).total_seconds() > constants.MESSAGE_VALIDITY_DURATION:
        raise UnauthorizedError(
            "Difference betweeen message time and server time is "
            f"greater than {constants.MESSAGE_VALIDITY_DURATION}s"
        )

    # verify account with username exists in database
    try:
        db_account = get_account_by_username(
            db_session,
            username=username,
            fetch_ssh_keys=True,
        )
    except RecordDoesNotExistError as exc:
        raise UnauthorizedError() from exc

    # verify signature of message with account's public keys
    authenticated = False
    ssh_keys = [ssh_key for worker in db_account.workers for ssh_key in worker.ssh_keys]
    for ssh_key in ssh_keys:
        try:
            if verify_signed_message(
                bytes(ssh_key.key, encoding="ascii"),
                signature,
                bytes(x_sshauth_message, encoding="ascii"),
            ):
                authenticated = True
                break
        except PublicKeyLoadError as exc:
            logger.exception("error while verifying message using public key")
            raise ForbiddenError("Unable to load public_key") from exc

    if not authenticated:
        raise UnauthorizedError("Could not find matching key for signature.")

    return _access_token_response(db_session, db_account, response)


@router.post("/oauth2")
def oauth2(
    credentials: OAuth2CredentialsWithPassword | OAuth2CredentialsWithRefreshToken,
    db_session: Annotated[OrmSession, Depends(gen_dbsession)],
    response: Response,
) -> Token:
    """Authorize an account with username and password."""
    if credentials.grant_type == "password":
        return _auth_with_credentials(db_session, credentials, response)
    elif credentials.grant_type == "refresh_token":
        return _refresh_access_token(db_session, credentials.refresh_token, response)
    else:
        raise BadRequestError("Invalid grant type")


@router.get("/test")
def test(
    _: Account = Depends(get_current_account),
):
    """Test if account's authentication tokens are still valid."""
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/me")
def get_current_account_info(
    current_account: Annotated[Account, Depends(get_current_account)],
) -> AccountSchema:
    """Get the current authenticated account's information including scopes."""
    return create_account_schema(current_account)
