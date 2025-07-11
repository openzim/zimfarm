from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from zimfarm_backend.common.roles import ROLES
from zimfarm_backend.common.schemas.fields import (
    LimitFieldMax200,
    SkipField,
)
from zimfarm_backend.common.schemas.models import calculate_pagination_metadata
from zimfarm_backend.db import gen_dbsession
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.models import User
from zimfarm_backend.db.ssh_key import (
    create_ssh_key,
    delete_ssh_key,
    get_ssh_key_by_fingerprint,
    get_ssh_key_by_fingerprint_or_none,
)
from zimfarm_backend.db.user import (
    check_user_permission,
    get_user_by_username,
    get_user_by_username_or_none,
)
from zimfarm_backend.db.user import create_user as db_create_user
from zimfarm_backend.db.user import delete_user as db_delete_user
from zimfarm_backend.db.user import get_users as db_get_users
from zimfarm_backend.db.user import update_user as db_update_user
from zimfarm_backend.db.user import update_user_password as db_update_user_password
from zimfarm_backend.exceptions import PEMPublicKeyLoadError
from zimfarm_backend.routes.dependencies import get_current_user
from zimfarm_backend.routes.http_errors import (
    BadRequestError,
    NotFoundError,
    UnauthorizedError,
)
from zimfarm_backend.routes.models import ListResponse
from zimfarm_backend.routes.users.models import (
    BaseUserWithSshKeysSchema,
    KeySchema,
    PasswordUpdateSchema,
    SshKeyList,
    SshKeyRead,
    UserCreateSchema,
    UserSchema,
    UserSchemaWithSshKeys,
    UserUpdateSchema,
)
from zimfarm_backend.utils.token import (
    get_public_key_fingerprint,
    load_rsa_public_key,
    serialize_rsa_public_key,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
def get_users(
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: Annotated[SkipField, Query()] = 0,
    limit: Annotated[LimitFieldMax200, Query()] = 20,
) -> ListResponse[UserSchema]:
    """Get a list of users"""
    if not check_user_permission(current_user, namespace="users", name="read"):
        raise UnauthorizedError("You are not allowed to access this resource")

    results = db_get_users(db_session, skip=skip, limit=limit)
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=skip,
            limit=limit,
            page_size=len(results.users),
        ),
        items=[UserSchema.model_validate(user) for user in results.users],
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
            scope=ROLES[user_schema.role],
        )
    except RecordAlreadyExistsError as exc:
        raise BadRequestError("User already exists") from exc

    return UserSchemaWithSshKeys(
        username=user.username,
        email=user.email,
        scope=user.scope,
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
        username=user.username,
        email=user.email,
        scope=user.scope,
        ssh_keys=[SshKeyRead.model_validate(ssh_key) for ssh_key in user.ssh_keys],
    )


@router.patch("/{username}")
def update_user(
    username: Annotated[str, Path()],
    user_schema: UserUpdateSchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Update a specific user"""
    try:
        user = get_user_by_username(db_session, username=username)
    except RecordDoesNotExistError as exc:
        raise NotFoundError("User not found") from exc

    if username != current_user.username:
        if not check_user_permission(current_user, namespace="users", name="update"):
            raise UnauthorizedError("You are not allowed to access this resource")

    db_update_user(
        db_session,
        user_id=user.id,
        email=user_schema.email,
        scope=ROLES.get(user_schema.role) if user_schema.role else None,
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete("/{username}")
def delete_user(
    username: Annotated[str, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Delete a specific user"""
    try:
        user = get_user_by_username(db_session, username=username)
    except RecordDoesNotExistError as exc:
        raise NotFoundError("User not found") from exc

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
    try:
        user = get_user_by_username(db_session, username=username)
    except RecordDoesNotExistError as exc:
        raise NotFoundError("User not found") from exc

    if username != current_user.username:
        if not check_user_permission(current_user, namespace="users", name="ssh_keys"):
            raise UnauthorizedError("You are not allowed to access this resource")

    try:
        rsa_public_key = load_rsa_public_key(ssh_key.key)
    except PEMPublicKeyLoadError as e:
        raise BadRequestError("Invalid RSA public key") from e

    fingerprint = get_public_key_fingerprint(rsa_public_key)

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
        pkcs8_key=serialize_rsa_public_key(rsa_public_key).decode("ascii"),
        name=ssh_key.name,
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

    try:
        user = get_user_by_username(db_session, username=username, fetch_ssh_keys=True)
    except RecordDoesNotExistError as exc:
        raise NotFoundError("User not found") from exc

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
    try:
        user = get_user_by_username(db_session, username=username)
    except RecordDoesNotExistError as exc:
        raise NotFoundError("User not found") from exc

    if current_user.username == username:
        if password_update.current is None:
            raise BadRequestError("You must enter your current password.")

        if not check_password_hash(
            current_user.password_hash or "", password_update.current
        ):
            raise UnauthorizedError()
    elif not check_user_permission(current_user, namespace="users", name="ssh_keys"):
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
    try:
        db_ssh_key = get_ssh_key_by_fingerprint(db_session, fingerprint=fingerprint)
    except RecordDoesNotExistError as exc:
        raise NotFoundError("SSH key not found") from exc

    if username != "-":
        try:
            get_user_by_username(db_session, username=username)
        except RecordDoesNotExistError as exc:
            raise NotFoundError("User not found") from exc

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

    try:
        user = get_user_by_username(db_session, username=username)
    except RecordDoesNotExistError as exc:
        raise NotFoundError("User not found") from exc

    try:
        get_ssh_key_by_fingerprint(db_session, fingerprint=fingerprint)
    except RecordDoesNotExistError as exc:
        raise NotFoundError("SSH key not found") from exc

    delete_ssh_key(db_session, fingerprint=fingerprint, user_id=user.id)
    return Response(status_code=HTTPStatus.NO_CONTENT)
