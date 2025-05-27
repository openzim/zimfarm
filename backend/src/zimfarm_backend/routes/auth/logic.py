import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session as OrmSession
from werkzeug.security import check_password_hash

from zimfarm_backend.db import gen_dbsession
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.refresh_token import (
    create_refresh_token,
    delete_refresh_token,
    expire_refresh_tokens,
    get_refresh_token,
)
from zimfarm_backend.db.user import get_user_by_username
from zimfarm_backend.routes.auth.models import CredentialsIn, Token
from zimfarm_backend.routes.http_errors import UnauthorizedError
from zimfarm_backend.settings import Settings
from zimfarm_backend.utils.token import generate_access_token

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
        expires_in=Settings.JWT_TOKEN_EXPIRY_DURATION,
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
        expires_in=Settings.JWT_TOKEN_EXPIRY_DURATION,
    )
