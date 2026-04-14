from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import selectinload

from zimfarm_backend.common import is_valid_uuid
from zimfarm_backend.common.roles import ROLES, RoleEnum, merge_scopes
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.models import AccountUpdateSchema
from zimfarm_backend.common.schemas.orms import AccountSchema
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.models import Account


def get_account_by_username_or_none(
    session: OrmSession, *, username: str, fetch_ssh_keys: bool = False
) -> Account | None:
    """Get an account by username or return None if the account does not exist"""
    stmt = select(Account).where(Account.username == username)
    if fetch_ssh_keys:
        stmt = stmt.options(selectinload(Account.ssh_keys))
    return session.scalars(stmt).one_or_none()


def get_account_by_username(
    session: OrmSession, *, username: str, fetch_ssh_keys: bool = False
) -> Account:
    """Get an account by username or raise an exception if the account does not exist"""
    if (
        account := get_account_by_username_or_none(
            session, username=username, fetch_ssh_keys=fetch_ssh_keys
        )
    ) is None:
        raise RecordDoesNotExistError(
            f"Account with username {username} does not exist"
        )
    return account


def get_account_by_id_or_none(
    session: OrmSession, *, account_id: UUID, fetch_ssh_keys: bool = False
) -> Account | None:
    """Get an account by id or return None if the account does not exist"""
    stmt = select(Account).where(
        (Account.id == account_id) | (Account.idp_sub == account_id)
    )
    if fetch_ssh_keys:
        stmt = stmt.options(selectinload(Account.ssh_keys))
    return session.scalars(stmt).one_or_none()


def get_account_by_id(
    session: OrmSession, *, account_id: UUID, fetch_ssh_keys: bool = False
) -> Account:
    """Get an account by id or raise an exception if the account does not exist"""
    if (
        account := get_account_by_id_or_none(
            session, account_id=account_id, fetch_ssh_keys=fetch_ssh_keys
        )
    ) is None:
        raise RecordDoesNotExistError(f"Account with id {account_id} does not exist")
    return account


def check_account_permission(
    account: Account,
    *,
    namespace: str,
    name: str,
) -> bool:
    """Check if an account has a permission for a given namespace and name"""
    # Select the scope that comes with their role enum or scope from the DB
    scope = ROLES.get(account.role, account.scope)
    if not scope:
        return False
    return scope.get(namespace, {}).get(name, False)


def update_account_password(
    session: OrmSession,
    *,
    account_id: UUID,
    password_hash: str | None,
) -> None:
    """Update an account's password"""
    session.execute(
        update(Account)
        .where(Account.id == account_id)
        .values(password_hash=password_hash)
    )


class AccountList(BaseModel):
    nb_records: int
    accounts: list[Account]


def create_account_schema(account: Account) -> AccountSchema:
    return AccountSchema(
        id=account.id,
        username=account.username,
        display_name=account.display_name,
        role=account.role,
        scope=merge_scopes(
            ROLES.get(account.role, account.scope or {}), ROLES[RoleEnum.ADMIN]
        ),
        idp_sub=account.idp_sub,
        has_ssh_keys=len(account.ssh_keys) > 0,
        has_password=account.password_hash is not None,
    )


def get_accounts(
    session: OrmSession, *, skip: int, limit: int, username: str | None = None
) -> AccountList:
    """Get a list of accounts"""
    query = (
        select(
            func.count().over().label("nb_records"),
            Account,
        )
        .where(
            Account.deleted.is_(False),
            (
                Account.display_name.ilike(
                    f"%{username if username is not None else ''}%"
                )
            )
            | (username is None),
        )
        .options(selectinload(Account.ssh_keys))
        .offset(skip)
        .limit(limit)
        .order_by(Account.display_name.asc(), Account.id.asc())
    )

    results = AccountList(nb_records=0, accounts=[])
    for nb_records, account in session.execute(query).all():
        results.nb_records = nb_records
        results.accounts.append(account)
    return results


def create_account(
    session: OrmSession,
    *,
    display_name: str,
    username: str | None = None,
    password_hash: str | None = None,
    scope: dict[str, Any] | None = None,
    role: str = "custom",
    idp_sub: UUID | None = None,
) -> Account:
    """Create a new account"""
    if role != "custom" and scope is not None:
        raise ValueError("No scopes should be defined for non-custom roles")
    account = Account(
        username=username,
        display_name=display_name,
        password_hash=password_hash,
        scope=scope,
        role=role,
        deleted=False,
        idp_sub=idp_sub,
    )
    session.add(account)
    try:
        session.flush()
    except IntegrityError as exc:
        raise RecordAlreadyExistsError("Account already exists") from exc
    return account


def update_account(
    session: OrmSession, *, account_id: str | UUID, request: AccountUpdateSchema
) -> None:
    """Update an account"""
    account = get_account_by_identifier(
        session, account_identifier=str(account_id), fetch_ssh_keys=True
    )

    if request.role is not None and request.scope is not None:
        raise ValueError("Only one of role/scope must be set.")

    values = request.model_dump(exclude_unset=True, mode="json")

    if "display_name" in values and not values["display_name"]:
        raise ValueError("Account must have a display name.")

    # Allow blank username only if an account does not have ssh key or password set.
    if (len(account.ssh_keys) > 0 or account.password_hash is not None) and (
        "username" in values and not values["username"]
    ):
        raise ValueError("Account with password/ssh key must have a username.")

    if (role := values.get("role")) is not None:
        values["role"] = role
        values["scope"] = None

    if (scope := values.get("scope")) is not None:
        values["role"] = "custom"
        values["scope"] = scope

    if not values:
        return

    session.execute(update(Account).where(Account.id == account.id).values(**values))


def delete_account(
    session: OrmSession,
    *,
    account_id: UUID,
) -> None:
    """Delete an account"""
    session.execute(
        update(Account).where(Account.id == account_id).values(deleted=True)
    )


def get_account_by_identifier_or_none(
    session: OrmSession, *, account_identifier: str, fetch_ssh_keys: bool = False
) -> Account | None:
    """Get an account or None by either username (str) or account_id (UUID)"""
    if is_valid_uuid(account_identifier):
        return get_account_by_id_or_none(
            session, account_id=UUID(account_identifier), fetch_ssh_keys=fetch_ssh_keys
        )

    return get_account_by_username_or_none(
        session, username=account_identifier, fetch_ssh_keys=fetch_ssh_keys
    )


def get_account_by_identifier(
    session: OrmSession, *, account_identifier: str, fetch_ssh_keys: bool = False
):
    """Get an account by either username(str) or account_id(UUID).

    Raises RecordDoestNotExistError if account not found.
    """
    if (
        account := get_account_by_identifier_or_none(
            session,
            account_identifier=account_identifier,
            fetch_ssh_keys=fetch_ssh_keys,
        )
    ) is None:
        raise RecordDoesNotExistError(
            f"Account with identifier {account_identifier} does not exist"
        )
    return account
