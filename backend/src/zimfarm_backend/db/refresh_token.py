import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.constants import REFRESH_TOKEN_EXPIRY_DURATION
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Refreshtoken
from zimfarm_backend.db.user import get_user_by_id


def get_refresh_token_or_none(session: OrmSession, token: UUID) -> Refreshtoken | None:
    """Get a refresh token by token"""
    return session.scalars(
        select(Refreshtoken).where(Refreshtoken.token == token)
    ).one_or_none()


def get_refresh_token(session: OrmSession, token: UUID) -> Refreshtoken:
    """Get a refresh token by token"""
    db_refresh_token = get_refresh_token_or_none(session, token)
    if db_refresh_token is None:
        raise RecordDoesNotExistError("Refresh token not found")
    return db_refresh_token


def create_refresh_token(session: OrmSession, user_id: UUID) -> Refreshtoken:
    """Create a refresh token for a user"""
    refresh_token = Refreshtoken(
        token=uuid4(),
        expire_time=getnow()
        + datetime.timedelta(seconds=REFRESH_TOKEN_EXPIRY_DURATION),
    )
    refresh_token.user = get_user_by_id(session, user_id=user_id)
    session.add(refresh_token)
    session.flush()
    return refresh_token


def delete_refresh_token(session: OrmSession, token: UUID) -> None:
    """Delete a refresh token by token"""
    db_refresh_token = get_refresh_token_or_none(session, token)
    if db_refresh_token is None:
        raise RecordDoesNotExistError("Refresh token not found")
    session.delete(db_refresh_token)
    session.flush()


def expire_refresh_tokens(session: OrmSession, expire_time: datetime.datetime) -> None:
    """Expire all refresh tokens before a given time"""
    for db_refresh_token in session.scalars(
        select(Refreshtoken).where(Refreshtoken.expire_time < expire_time)
    ):
        session.delete(db_refresh_token)
    session.flush()
