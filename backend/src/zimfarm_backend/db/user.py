from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import selectinload

from zimfarm_backend.common.roles import ROLES, RoleEnum, merge_scopes
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.models import UserUpdateSchema
from zimfarm_backend.common.schemas.orms import UserSchema
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
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


def get_user_by_idp_sub_or_none(
    session: OrmSession, *, idp_sub: UUID, fetch_ssh_keys: bool = False
) -> User | None:
    """Get a user by IDP sub or return None if the user does not exist"""
    stmt = select(User).where(User.idp_sub == idp_sub)
    if fetch_ssh_keys:
        stmt = stmt.options(selectinload(User.ssh_keys))
    return session.scalars(stmt).one_or_none()


def get_user_by_idp_sub(
    session: OrmSession, *, idp_sub: UUID, fetch_ssh_keys: bool = False
) -> User:
    """Get a user by IDP sub or raise an exception if the user does not exist"""
    if (
        user := get_user_by_idp_sub_or_none(
            session, idp_sub=idp_sub, fetch_ssh_keys=fetch_ssh_keys
        )
    ) is None:
        raise RecordDoesNotExistError(f"User with idp_sub {idp_sub} does not exist")
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


def check_user_permission(
    user: User,
    *,
    namespace: str,
    name: str,
) -> bool:
    """Check if a user has a permission for a given namespace and name"""
    # Select the scope that comes with their role enum or scope from the DB
    scope = ROLES.get(user.role, user.scope)
    if not scope:
        return False
    return scope.get(namespace, {}).get(name, False)


def update_user_password(
    session: OrmSession,
    *,
    user_id: UUID,
    password_hash: str,
) -> None:
    """Update a user's password"""
    session.execute(
        update(User).where(User.id == user_id).values(password_hash=password_hash)
    )


class UserList(BaseModel):
    nb_records: int
    users: list[User]


def create_user_schema(user: User) -> UserSchema:
    return UserSchema(
        username=user.username,
        email=user.email,
        role=user.role,
        scope=merge_scopes(
            ROLES.get(user.role, user.scope or {}), ROLES[RoleEnum.ADMIN]
        ),
        idp_sub=user.idp_sub,
    )


def get_users(
    session: OrmSession, *, skip: int, limit: int, username: str | None = None
) -> UserList:
    """Get a list of users"""
    query = (
        select(
            func.count().over().label("nb_records"),
            User,
        )
        .where(
            User.deleted.is_(False),
            (User.username.ilike(f"%{username if username is not None else ''}%"))
            | (username is None),
        )
        .offset(skip)
        .limit(limit)
        .order_by(User.username.asc(), User.id.asc())
    )

    results = UserList(nb_records=0, users=[])
    for nb_records, user in session.execute(query).all():
        results.nb_records = nb_records
        results.users.append(user)
    return results


def create_user(
    session: OrmSession,
    *,
    username: str,
    email: str | None = None,
    password_hash: str | None = None,
    scope: dict[str, Any] | None = None,
    role: str = "custom",
    idp_sub: UUID | None = None,
) -> User:
    """Create a new user"""
    if role != "custom" and scope is not None:
        raise ValueError("No scopes should be defined for non-custom roles")
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        scope=scope,
        role=role,
        deleted=False,
        idp_sub=idp_sub,
    )
    session.add(user)
    try:
        session.flush()
    except IntegrityError as exc:
        raise RecordAlreadyExistsError("User already exists") from exc
    return user


def update_user(
    session: OrmSession, *, user_id: UUID, request: UserUpdateSchema
) -> None:
    """Update a user"""

    if request.role is not None and request.scope is not None:
        raise ValueError("Only one of role/scope must be set.")

    values = request.model_dump(exclude_unset=True)

    if (role := values.get("role")) is not None:
        values["role"] = role
        values["scope"] = None

    if (scope := values.get("scope")) is not None:
        values["role"] = "custom"
        values["scope"] = scope

    if not values:
        return
    session.execute(update(User).where(User.id == user_id).values(**values))


def delete_user(
    session: OrmSession,
    *,
    user_id: UUID,
) -> None:
    """Delete a user"""
    session.execute(update(User).where(User.id == user_id).values(deleted=True))
