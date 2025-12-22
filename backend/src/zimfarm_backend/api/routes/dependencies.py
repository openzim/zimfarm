import datetime
import uuid
from typing import Annotated, Literal

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import exceptions as jwt_exceptions
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.constants import JWT_SECRET
from zimfarm_backend.api.routes.http_errors import UnauthorizedError
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.db import gen_dbsession, gen_manual_dbsession
from zimfarm_backend.db.models import User
from zimfarm_backend.db.user import check_user_permission, get_user_by_id_or_none

security = HTTPBearer(description="Access Token", auto_error=False)
AuthorizationCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(security)
]


class JWTClaims(BaseModel):
    iss: str
    exp: datetime.datetime
    iat: datetime.datetime
    subject: uuid.UUID


def get_jwt_claims_or_none(
    authorization: AuthorizationCredentials,
) -> JWTClaims | None:
    """
    Get the JWT claims or None if the user is not authenticated
    """
    if authorization is None:
        return None
    token = authorization.credentials
    try:
        jwt_claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt_exceptions.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token has expired.") from exc
    except (jwt_exceptions.InvalidTokenError, jwt_exceptions.PyJWTError) as exc:
        raise UnauthorizedError from exc

    try:
        claims = JWTClaims(**jwt_claims)
    except PydanticValidationError as exc:
        raise UnauthorizedError from exc
    return claims


def get_current_user_or_none_with_session(
    session_type: Literal["auto", "manual"] = "auto",
):
    def _get_current_user_or_none(
        claims: Annotated[JWTClaims | None, Depends(get_jwt_claims_or_none)],
        session: Annotated[
            OrmSession,
            Depends(gen_dbsession if session_type == "auto" else gen_manual_dbsession),
        ],
    ) -> User | None:
        if claims is None:
            return None
        return get_user_by_id_or_none(session, user_id=claims.subject)

    return _get_current_user_or_none


def get_current_user_with_session(
    session_type: Literal["auto", "manual"] = "auto",
):
    def _get_current_user(
        user: Annotated[
            User | None,
            Depends(get_current_user_or_none_with_session(session_type=session_type)),
        ],
    ) -> User:
        if user is None:
            raise UnauthorizedError()

        if user.deleted:
            raise UnauthorizedError()

        return user

    return _get_current_user


# Convenience functions for common cases
get_current_user_or_none = get_current_user_or_none_with_session(session_type="auto")
get_current_user = get_current_user_with_session(session_type="auto")


def require_permission(*, namespace: str, name: str):
    """
    checks if the current user has a specific permission.
    """

    def _check_permission(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if not check_user_permission(current_user, namespace=namespace, name=name):
            raise UnauthorizedError(
                "You do not have permission to perform this action. "
            )
        return current_user

    return _check_permission
