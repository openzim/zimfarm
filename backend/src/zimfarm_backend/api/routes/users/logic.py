from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from zimfarm_backend.api.routes.dependencies import get_current_user
from zimfarm_backend.api.routes.http_errors import (
    BadRequestError,
    NotFoundError,
    UnauthorizedError,
)
from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.api.routes.users.models import (
    KeySchema,
    PasswordUpdateSchema,
    UserCreateSchema,
    UsersGetSchema,
    UserUpdateSchema,
)
from zimfarm_backend.common.schemas.models import calculate_pagination_metadata
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
    get_user_by_username,
    get_user_by_username_or_none,
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
            email=user_schema.email,
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


@router.get("/{username}")
def get_user(
    username: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserSchemaWithSshKeys:
    """Get a specific user"""
    if username != current_user.username:
        if not check_user_permission(current_user, namespace="users", name="read"):
            raise UnauthorizedError("You are not allowed to access this resource")

    user = get_user_by_username_or_none(db_session, username=username)
    if not user:
        raise NotFoundError("User not found")

    return UserSchemaWithSshKeys(
        **create_user_schema(user).model_dump(),
        ssh_keys=[SshKeyRead.model_validate(ssh_key) for ssh_key in user.ssh_keys],
    )


@router.patch("/{username}")
def update_user(
    username: Annotated[str, Path()],
    request: UserUpdateSchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Update a specific user"""
    user = get_user_by_username(db_session, username=username)

    if username != current_user.username:
        if not check_user_permission(current_user, namespace="users", name="update"):
            raise UnauthorizedError("You are not allowed to access this resource")

    db_update_user(
        db_session,
        user_id=user.id,
        request=request,
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete("/{username}")
def delete_user(
    username: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Delete a specific user"""
    user = get_user_by_username(db_session, username=username)

    if not check_user_permission(current_user, namespace="users", name="delete"):
        raise UnauthorizedError("You are not allowed to access this resource")

    db_delete_user(db_session, user_id=user.id)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post("/{username}/keys")
def create_user_key(
    username: Annotated[str, Path()],
    ssh_key: KeySchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SshKeyRead:
    """Create a new SSH key for a user"""
    user = get_user_by_username(db_session, username=username)

    if username != current_user.username:
        if not check_user_permission(current_user, namespace="users", name="ssh_keys"):
            raise UnauthorizedError("You are not allowed to access this resource")

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


@router.get("/{username}/keys")
def get_user_keys(
    username: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SshKeyList:
    """Get a list of SSH keys for a user"""
    if username != current_user.username:
        if not check_user_permission(current_user, namespace="users", name="ssh_keys"):
            raise UnauthorizedError("You are not allowed to access this resource")

    user = get_user_by_username(db_session, username=username, fetch_ssh_keys=True)

    return SshKeyList(
        ssh_keys=[SshKeyRead.model_validate(ssh_key) for ssh_key in user.ssh_keys]
    )


@router.patch("/{username}/password")
def update_user_password(
    username: Annotated[str, Path()],
    password_update: PasswordUpdateSchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Update a user's password"""
    user = get_user_by_username(db_session, username=username)

    if current_user.username == username:
        if password_update.current is None:
            raise BadRequestError("You must enter your current password.")

        if not check_password_hash(
            current_user.password_hash or "", password_update.current
        ):
            raise BadRequestError()
    elif not check_user_permission(
        current_user, namespace="users", name="change_password"
    ):
        raise UnauthorizedError("You are not allowed to access this resource")

    db_update_user_password(
        db_session,
        user_id=user.id,
        password_hash=generate_password_hash(password_update.new),
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/{username}/keys/{fingerprint:path}")
def get_user_key(
    username: Annotated[str, Path()],
    fingerprint: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
    with_permission: Annotated[list[str] | None, Query()] = None,
) -> BaseUserWithSshKeysSchema:
    """Get a specific SSH key for a user"""
    db_ssh_key = get_ssh_key_by_fingerprint(db_session, fingerprint=fingerprint)

    if username != "-":
        get_user_by_username(db_session, username=username)

    requested_permissions = with_permission or []
    for permission in requested_permissions:
        namespace, perm_name = permission.split(".", 1)
        if db_ssh_key.user.scope and not db_ssh_key.user.scope.get(namespace, {}).get(
            perm_name
        ):
            raise UnauthorizedError(permission)

    return BaseUserWithSshKeysSchema(
        username=db_ssh_key.user.username,
        key=db_ssh_key.key,
        name=db_ssh_key.name,
        type=db_ssh_key.type,
    )


@router.delete("/{username}/keys/{fingerprint:path}")
def delete_user_key(
    username: Annotated[str, Path()],
    fingerprint: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Delete a specific SSH key for a user"""
    if current_user.username != username:
        if not check_user_permission(current_user, namespace="users", name="ssh_keys"):
            raise UnauthorizedError("You are not allowed to access this resource")

    user = get_user_by_username(db_session, username=username)

    get_ssh_key_by_fingerprint(db_session, fingerprint=fingerprint)

    delete_ssh_key(db_session, fingerprint=fingerprint, user_id=user.id)
    return Response(status_code=HTTPStatus.NO_CONTENT)
