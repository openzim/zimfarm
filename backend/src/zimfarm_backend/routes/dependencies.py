import datetime
import uuid
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import exceptions as jwt_exceptions
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.constants import JWT_SECRET
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.db import gen_dbsession
from zimfarm_backend.db.models import User
from zimfarm_backend.db.user import get_user_by_id_or_none
from zimfarm_backend.routes.http_errors import UnauthorizedError

security = HTTPBearer(description="Access Token")
AuthorizationCredentials = Annotated[HTTPAuthorizationCredentials, Depends(security)]


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


def get_current_user_or_none(
    claims: Annotated[JWTClaims, Depends(get_jwt_claims_or_none)],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> User | None:
    """
    Get the current user or None if the user is not authenticated
    """
    return get_user_by_id_or_none(session, user_id=claims.subject)


def get_current_user(
    user: Annotated[User | None, Depends(get_current_user_or_none)],
) -> User:
    """
    Get the current user
    """
    if user is None:
        raise UnauthorizedError()

    if user.deleted:
        raise UnauthorizedError()

    return user
