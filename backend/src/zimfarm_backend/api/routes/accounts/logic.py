from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from zimfarm_backend.api.routes.accounts.models import (
    AccountCreateSchema,
    AccountsGetSchema,
    KeySchema,
    PasswordUpdateSchema,
)
from zimfarm_backend.api.routes.dependencies import (
    get_current_account,
    require_permission,
    require_permission_if_not_self,
)
from zimfarm_backend.api.routes.http_errors import (
    BadRequestError,
    UnauthorizedError,
)
from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.common.schemas.models import (
    AccountUpdateSchema,
    calculate_pagination_metadata,
)
from zimfarm_backend.common.schemas.orms import (
    AccountSchema,
    AccountSchemaWithSshKeys,
    BaseAccountWithSshKeysSchema,
    SshKeyList,
    SshKeyRead,
)
from zimfarm_backend.db import gen_dbsession
from zimfarm_backend.db.account import create_account as db_create_account
from zimfarm_backend.db.account import (
    create_account_schema,
    get_account_by_identifier,
)
from zimfarm_backend.db.account import delete_account as db_delete_account
from zimfarm_backend.db.account import get_accounts as db_get_accounts
from zimfarm_backend.db.account import update_account as db_update_account
from zimfarm_backend.db.account import (
    update_account_password as db_update_account_password,
)
from zimfarm_backend.db.exceptions import RecordAlreadyExistsError
from zimfarm_backend.db.models import Account
from zimfarm_backend.db.ssh_key import (
    create_ssh_key,
    delete_ssh_key,
    get_ssh_key_by_fingerprint,
    get_ssh_key_by_fingerprint_or_none,
)
from zimfarm_backend.exceptions import PublicKeyLoadError
from zimfarm_backend.utils.cryptography import (
    get_public_key_fingerprint,
    get_public_key_type,
    load_public_key,
)

router = APIRouter(prefix="/accounts", tags=["accounts"])
users_router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get(
    "", dependencies=[Depends(require_permission(namespace="accounts", name="read"))]
)
@users_router.get(
    "", dependencies=[Depends(require_permission(namespace="accounts", name="read"))]
)
def get_accounts(
    db_session: Annotated[Session, Depends(gen_dbsession)],
    params: Annotated[AccountsGetSchema, Query()],
) -> ListResponse[AccountSchema]:
    """Get a list of accounts"""
    results = db_get_accounts(
        db_session, skip=params.skip, limit=params.limit, username=params.username
    )
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=params.skip,
            limit=params.limit,
            page_size=len(results.accounts),
        ),
        items=[create_account_schema(account) for account in results.accounts],
    )


@router.post(
    "", dependencies=[Depends(require_permission(namespace="accounts", name="create"))]
)
@users_router.post(
    "", dependencies=[Depends(require_permission(namespace="accounts", name="create"))]
)
def create_account(
    user_schema: AccountCreateSchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
) -> AccountSchemaWithSshKeys:
    try:
        account = db_create_account(
            db_session,
            username=user_schema.username,
            display_name=user_schema.username,
            password_hash=generate_password_hash(user_schema.password),
            scope=None,
            role=user_schema.role,
        )
    except RecordAlreadyExistsError as exc:
        raise BadRequestError("Account already exists") from exc

    return AccountSchemaWithSshKeys(
        **create_account_schema(account).model_dump(),
        ssh_keys=[SshKeyRead.model_validate(ssh_key) for ssh_key in account.ssh_keys],
    )


@router.get(
    "/{account_identifier}",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="accounts", name="read"))
    ],
)
@users_router.get(
    "/{account_identifier}",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="accounts", name="read"))
    ],
)
def get_account(
    account_identifier: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
) -> AccountSchemaWithSshKeys:
    """Get a specific account"""
    account = get_account_by_identifier(
        db_session, account_identifier=account_identifier, fetch_ssh_keys=True
    )

    return AccountSchemaWithSshKeys(
        **create_account_schema(account).model_dump(),
        ssh_keys=[SshKeyRead.model_validate(ssh_key) for ssh_key in account.ssh_keys],
    )


@router.patch(
    "/{account_identifier}",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="accounts", name="update"))
    ],
)
@users_router.patch(
    "/{account_identifier}",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="accounts", name="update"))
    ],
)
def update_account(
    account_identifier: Annotated[str, Path()],
    request: AccountUpdateSchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
) -> Response:
    """Update a specific account"""
    db_update_account(
        db_session,
        account_id=account_identifier,
        request=request,
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete(
    "/{account_identifier}",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="accounts", name="delete"))
    ],
)
@users_router.delete(
    "/{account_identifier}",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="accounts", name="delete"))
    ],
)
def delete_account(
    account_identifier: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
) -> Response:
    """Delete a specific account"""
    account = get_account_by_identifier(
        db_session, account_identifier=account_identifier
    )
    db_delete_account(db_session, account_id=account.id)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post(
    "/{account_identifier}/keys",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="accounts", name="ssh_keys"))
    ],
)
@users_router.post(
    "/{account_identifier}/keys",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="accounts", name="ssh_keys"))
    ],
)
def create_account_key(
    account_identifier: Annotated[str, Path()],
    ssh_key: KeySchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
) -> SshKeyRead:
    """Create a new SSH key for an account"""
    account = get_account_by_identifier(
        db_session, account_identifier=account_identifier
    )
    if not account.username:
        raise BadRequestError("Only accounts with username can have SSH keys.")

    try:
        public_key = load_public_key(bytes(ssh_key.key, encoding="ascii"))
    except PublicKeyLoadError as e:
        raise BadRequestError("Invalid public key") from e

    fingerprint = get_public_key_fingerprint(public_key)

    # check if key already exists
    db_ssh_key = get_ssh_key_by_fingerprint_or_none(db_session, fingerprint=fingerprint)
    if db_ssh_key and db_ssh_key.account.id == account.id:
        raise BadRequestError("SSH key already exists")

    # add new ssh key to database
    db_ssh_key = create_ssh_key(
        db_session,
        fingerprint=fingerprint,
        account_id=account.id,
        key=ssh_key.key,
        name=ssh_key.name,
        type_=get_public_key_type(public_key),
    )
    return SshKeyRead.model_validate(db_ssh_key)


@router.get(
    "/{account_identifier}/keys",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="accounts", name="ssh_keys"))
    ],
)
@users_router.get(
    "/{account_identifier}/keys",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="accounts", name="ssh_keys"))
    ],
)
def get_account_keys(
    account_identifier: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
) -> SshKeyList:
    """Get a list of SSH keys for an account"""
    account = get_account_by_identifier(
        db_session, account_identifier=account_identifier, fetch_ssh_keys=True
    )
    return SshKeyList(
        ssh_keys=[SshKeyRead.model_validate(ssh_key) for ssh_key in account.ssh_keys]
    )


@router.patch(
    "/{account_identifier}/password",
    dependencies=[
        Depends(
            require_permission_if_not_self(namespace="accounts", name="change_password")
        )
    ],
)
@users_router.patch(
    "/{account_identifier}/password",
    dependencies=[
        Depends(
            require_permission_if_not_self(namespace="accounts", name="change_password")
        )
    ],
)
def update_account_password(
    account_identifier: Annotated[str, Path()],
    password_update: PasswordUpdateSchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> Response:
    """Update an account's password"""
    account = get_account_by_identifier(
        db_session, account_identifier=account_identifier
    )
    if not account.username:
        raise BadRequestError("Only accounts with username can have passwords.")

    # Accounts changing their own password must provide their password if one exists and
    # it must match the existing one
    if current_account.id == account.id and account.password_hash is not None:
        if password_update.current is None:
            raise BadRequestError("You must enter your current password.")

        if not check_password_hash(account.password_hash, password_update.current):
            raise BadRequestError()

    db_update_account_password(
        db_session,
        account_id=account.id,
        password_hash=(
            generate_password_hash(password_update.new) if password_update.new else None
        ),
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/{account_identifier}/keys/{fingerprint:path}")
@users_router.get("/{account_identifier}/keys/{fingerprint:path}")
def get_account_key(
    account_identifier: Annotated[str, Path()],
    fingerprint: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
    with_permission: Annotated[list[str] | None, Query()] = None,
) -> BaseAccountWithSshKeysSchema:
    """Get a specific SSH key for an account"""
    db_ssh_key = get_ssh_key_by_fingerprint(db_session, fingerprint=fingerprint)

    if account_identifier != "-":
        get_account_by_identifier(db_session, account_identifier=account_identifier)

    requested_permissions = with_permission or []
    for permission in requested_permissions:
        namespace, perm_name = permission.split(".", 1)
        if db_ssh_key.account.scope and not db_ssh_key.account.scope.get(
            namespace, {}
        ).get(perm_name):
            raise UnauthorizedError(permission)

    return BaseAccountWithSshKeysSchema(
        id=db_ssh_key.account.id,
        username=db_ssh_key.account.username,
        has_ssh_keys=True,
        has_password=db_ssh_key.account.password_hash is not None,
        display_name=db_ssh_key.account.display_name,
        key=db_ssh_key.key,
        name=db_ssh_key.name,
        type=db_ssh_key.type,
    )


@router.delete(
    "/{account_identifier}/keys/{fingerprint:path}",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="accounts", name="ssh_keys"))
    ],
)
@users_router.delete(
    "/{account_identifier}/keys/{fingerprint:path}",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="accounts", name="ssh_keys"))
    ],
)
def delete_account_key(
    account_identifier: Annotated[str, Path()],
    fingerprint: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
) -> Response:
    """Delete a specific SSH key for an account"""
    account = get_account_by_identifier(
        db_session, account_identifier=account_identifier
    )

    get_ssh_key_by_fingerprint(db_session, fingerprint=fingerprint)

    delete_ssh_key(db_session, fingerprint=fingerprint, account_id=account.id)
    return Response(status_code=HTTPStatus.NO_CONTENT)
