from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import selectinload

from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import User


def get_user_by_username_or_none(
    session: OrmSession, *, username: str, fetch_ssh_keys: bool = False
) -> User | None:
    """Get a user by username or return None if the user does not exist"""
    stmt = select(User).where(User.username == username)
    if fetch_ssh_keys:
        stmt = stmt.options(selectinload(User.ssh_keys))
    return session.scalars(stmt).one_or_none()


def get_user_by_username(
    session: OrmSession, *, username: str, fetch_ssh_keys: bool = False
) -> User:
    """Get a user by username or raise an exception if the user does not exist"""
    if (
        user := get_user_by_username_or_none(
            session, username=username, fetch_ssh_keys=fetch_ssh_keys
        )
    ) is None:
        raise RecordDoesNotExistError(f"User with username {username} does not exist")
    return user


def get_user_by_id_or_none(
    session: OrmSession, *, user_id: UUID, fetch_ssh_keys: bool = False
) -> User | None:
    """Get a user by id or return None if the user does not exist"""
    stmt = select(User).where(User.id == user_id)
    if fetch_ssh_keys:
        stmt = stmt.options(selectinload(User.ssh_keys))
    return session.scalars(stmt).one_or_none()


def get_user_by_id(
    session: OrmSession, *, user_id: UUID, fetch_ssh_keys: bool = False
) -> User:
    """Get a user by id or raise an exception if the user does not exist"""
    if (
        user := get_user_by_id_or_none(
            session, user_id=user_id, fetch_ssh_keys=fetch_ssh_keys
        )
    ) is None:
        raise RecordDoesNotExistError(f"User with id {user_id} does not exist")
    return user
