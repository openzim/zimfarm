from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from zimfarm_backend.api.routes.dependencies import (
    get_current_user,
    require_permission_if_not_self,
)
from zimfarm_backend.api.routes.http_errors import (
    BadRequestError,
    UnauthorizedError,
)
from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.api.routes.users.models import (
    KeySchema,
    PasswordUpdateSchema,
    UserCreateSchema,
    UsersGetSchema,
)
from zimfarm_backend.common.schemas.models import (
    UserUpdateSchema,
    calculate_pagination_metadata,
)
from zimfarm_backend.common.schemas.orms import (
    BaseUserWithSshKeysSchema,
    SshKeyList,
    SshKeyRead,
    UserSchema,
    UserSchemaWithSshKeys,
)
from zimfarm_backend.db import gen_dbsession
from zimfarm_backend.db.exceptions import RecordAlreadyExistsError
from zimfarm_backend.db.models import User
from zimfarm_backend.db.ssh_key import (
    create_ssh_key,
    delete_ssh_key,
    get_ssh_key_by_fingerprint,
    get_ssh_key_by_fingerprint_or_none,
)
from zimfarm_backend.db.user import (
    check_user_permission,
    create_user_schema,
    get_user_by_identifier,
)
from zimfarm_backend.db.user import create_user as db_create_user
from zimfarm_backend.db.user import delete_user as db_delete_user
from zimfarm_backend.db.user import get_users as db_get_users
from zimfarm_backend.db.user import update_user as db_update_user
from zimfarm_backend.db.user import update_user_password as db_update_user_password
from zimfarm_backend.exceptions import PublicKeyLoadError
from zimfarm_backend.utils.cryptography import (
    get_public_key_fingerprint,
    get_public_key_type,
    load_public_key,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
def get_users(
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
    params: Annotated[UsersGetSchema, Query()],
) -> ListResponse[UserSchema]:
    """Get a list of users"""
    if not check_user_permission(current_user, namespace="users", name="read"):
        raise UnauthorizedError("You are not allowed to access this resource")

    results = db_get_users(
        db_session, skip=params.skip, limit=params.limit, username=params.username
    )
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=params.skip,
            limit=params.limit,
            page_size=len(results.users),
        ),
        items=[create_user_schema(user) for user in results.users],
    )


@router.post("")
def create_user(
    user_schema: UserCreateSchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserSchemaWithSshKeys:
    if not check_user_permission(current_user, namespace="users", name="create"):
        raise UnauthorizedError("You are not allowed to create a user")

    try:
        user = db_create_user(
            db_session,
            username=user_schema.username,
            display_name=user_schema.username,
            password_hash=generate_password_hash(user_schema.password),
            scope=None,
            role=user_schema.role,
        )
    except RecordAlreadyExistsError as exc:
        raise BadRequestError("User already exists") from exc

    return UserSchemaWithSshKeys(
        **create_user_schema(user).model_dump(),
        ssh_keys=[SshKeyRead.model_validate(ssh_key) for ssh_key in user.ssh_keys],
    )


@router.get(
    "/{user_identifier}",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="users", name="read"))
    ],
)
def get_user(
    user_identifier: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
) -> UserSchemaWithSshKeys:
    """Get a specific user"""
    user = get_user_by_identifier(
        db_session, user_identifier=user_identifier, fetch_ssh_keys=True
    )

    return UserSchemaWithSshKeys(
        **create_user_schema(user).model_dump(),
        ssh_keys=[SshKeyRead.model_validate(ssh_key) for ssh_key in user.ssh_keys],
    )


@router.patch(
    "/{user_identifier}",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="users", name="update"))
    ],
)
def update_user(
    user_identifier: Annotated[str, Path()],
    request: UserUpdateSchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
) -> Response:
    """Update a specific user"""
    db_update_user(
        db_session,
        user_id=user_identifier,
        request=request,
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete(
    "/{user_identifier}",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="users", name="delete"))
    ],
)
def delete_user(
    user_identifier: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
) -> Response:
    """Delete a specific user"""
    user = get_user_by_identifier(db_session, user_identifier=user_identifier)
    db_delete_user(db_session, user_id=user.id)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post(
    "/{user_identifier}/keys",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="users", name="ssh_keys"))
    ],
)
def create_user_key(
    user_identifier: Annotated[str, Path()],
    ssh_key: KeySchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
) -> SshKeyRead:
    """Create a new SSH key for a user"""
    user = get_user_by_identifier(db_session, user_identifier=user_identifier)
    if not user.username:
        raise BadRequestError("Only users with username can have SSH keys.")

    try:
        public_key = load_public_key(bytes(ssh_key.key, encoding="ascii"))
    except PublicKeyLoadError as e:
        raise BadRequestError("Invalid public key") from e

    fingerprint = get_public_key_fingerprint(public_key)

    # check if key already exists
    db_ssh_key = get_ssh_key_by_fingerprint_or_none(db_session, fingerprint=fingerprint)
    if db_ssh_key and db_ssh_key.user.id == user.id:
        raise BadRequestError("SSH key already exists")

    # add new ssh key to database
    db_ssh_key = create_ssh_key(
        db_session,
        fingerprint=fingerprint,
        user_id=user.id,
        key=ssh_key.key,
        name=ssh_key.name,
        type_=get_public_key_type(public_key),
    )
    return SshKeyRead.model_validate(db_ssh_key)


@router.get(
    "/{user_identifier}/keys",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="users", name="ssh_keys"))
    ],
)
def get_user_keys(
    user_identifier: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
) -> SshKeyList:
    """Get a list of SSH keys for a user"""
    user = get_user_by_identifier(
        db_session, user_identifier=user_identifier, fetch_ssh_keys=True
    )
    return SshKeyList(
        ssh_keys=[SshKeyRead.model_validate(ssh_key) for ssh_key in user.ssh_keys]
    )


@router.patch(
    "/{user_identifier}/password",
    dependencies=[
        Depends(
            require_permission_if_not_self(namespace="users", name="change_password")
        )
    ],
)
def update_user_password(
    user_identifier: Annotated[str, Path()],
    password_update: PasswordUpdateSchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Update a user's password"""
    user = get_user_by_identifier(db_session, user_identifier=user_identifier)
    if not user.username:
        raise BadRequestError("Only users with username can have passwords.")

    # Users changing their own password must provide their password if one exists and
    # it must match the existing one
    if current_user.id == user.id and user.password_hash is not None:
        if password_update.current is None:
            raise BadRequestError("You must enter your current password.")

        if not check_password_hash(user.password_hash, password_update.current):
            raise BadRequestError()

    db_update_user_password(
        db_session,
        user_id=user.id,
        password_hash=(
            generate_password_hash(password_update.new) if password_update.new else None
        ),
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/{user_identifier}/keys/{fingerprint:path}")
def get_user_key(
    user_identifier: Annotated[str, Path()],
    fingerprint: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
    with_permission: Annotated[list[str] | None, Query()] = None,
) -> BaseUserWithSshKeysSchema:
    """Get a specific SSH key for a user"""
    db_ssh_key = get_ssh_key_by_fingerprint(db_session, fingerprint=fingerprint)

    if user_identifier != "-":
        get_user_by_identifier(db_session, user_identifier=user_identifier)

    requested_permissions = with_permission or []
    for permission in requested_permissions:
        namespace, perm_name = permission.split(".", 1)
        if db_ssh_key.user.scope and not db_ssh_key.user.scope.get(namespace, {}).get(
            perm_name
        ):
            raise UnauthorizedError(permission)

    return BaseUserWithSshKeysSchema(
        id=db_ssh_key.user.id,
        username=db_ssh_key.user.username,
        has_ssh_keys=True,
        has_password=db_ssh_key.user.password_hash is not None,
        display_name=db_ssh_key.user.display_name,
        key=db_ssh_key.key,
        name=db_ssh_key.name,
        type=db_ssh_key.type,
    )


@router.delete(
    "/{user_identifier}/keys/{fingerprint:path}",
    dependencies=[
        Depends(require_permission_if_not_self(namespace="users", name="ssh_keys"))
    ],
)
def delete_user_key(
    user_identifier: Annotated[str, Path()],
    fingerprint: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
) -> Response:
    """Delete a specific SSH key for a user"""
    user = get_user_by_identifier(db_session, user_identifier=user_identifier)

    get_ssh_key_by_fingerprint(db_session, fingerprint=fingerprint)

    delete_ssh_key(db_session, fingerprint=fingerprint, user_id=user.id)
    return Response(status_code=HTTPStatus.NO_CONTENT)
