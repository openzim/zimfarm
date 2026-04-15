from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from zimfarm_backend.api.routes.accounts.models import (
    AccountCreateSchema,
    AccountsGetSchema,
    PasswordUpdateSchema,
)
from zimfarm_backend.api.routes.dependencies import (
    get_current_account,
    require_permission,
)
from zimfarm_backend.api.routes.http_errors import (
    BadRequestError,
    ForbiddenError,
)
from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.common import is_valid_uuid
from zimfarm_backend.common.schemas.models import (
    AccountUpdateSchema,
    calculate_pagination_metadata,
)
from zimfarm_backend.common.schemas.orms import AccountSchema
from zimfarm_backend.db import gen_dbsession
from zimfarm_backend.db.account import (
    check_account_permission,
    create_account_schema,
    get_account_by_identifier,
)
from zimfarm_backend.db.account import create_account as db_create_account
from zimfarm_backend.db.account import delete_account as db_delete_account
from zimfarm_backend.db.account import get_accounts as db_get_accounts
from zimfarm_backend.db.account import update_account as db_update_account
from zimfarm_backend.db.account import (
    update_account_password as db_update_account_password,
)
from zimfarm_backend.db.exceptions import RecordAlreadyExistsError
from zimfarm_backend.db.models import Account

router = APIRouter(prefix="/accounts", tags=["accounts"])


def require_permission_if_not_self(namespace: str, name: str):
    """Ensure that an account has permission to access another account's resource.

    This uses the identifier in the path parameter to check against the current
    user.
    """

    def _require_permission_if_not_self(
        account_identifier: Annotated[str, Path()],
        current_account: Annotated[Account, Depends(get_current_account)],
    ):
        if (
            is_valid_uuid(account_identifier)
            and account_identifier != str(current_account.id)
        ) or (account_identifier != current_account.username):
            if not check_account_permission(
                current_account, namespace=namespace, name=name
            ):
                raise ForbiddenError("You are not allowed to access this resource")

    return _require_permission_if_not_self


@router.get(
    "", dependencies=[Depends(require_permission(namespace="accounts", name="read"))]
)
def get_accounts(
    db_session: Annotated[Session, Depends(gen_dbsession)],
    params: Annotated[AccountsGetSchema, Query()],
) -> ListResponse[AccountSchema]:
    """Get a list of accounts"""
    results = db_get_accounts(
        db_session,
        skip=params.skip,
        limit=params.limit,
        username=params.username,
        show_workers=params.show_workers,
        show_viewers=params.show_viewers,
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
def create_account(
    user_schema: AccountCreateSchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
) -> AccountSchema:
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

    return create_account_schema(account)


@router.get(
    "/{account_identifier}",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="accounts", name="read"))
    ],
)
def get_account(
    account_identifier: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
) -> AccountSchema:
    """Get a specific account"""
    account = get_account_by_identifier(
        db_session, account_identifier=account_identifier
    )
    return create_account_schema(account)


@router.patch(
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


@router.patch(
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
