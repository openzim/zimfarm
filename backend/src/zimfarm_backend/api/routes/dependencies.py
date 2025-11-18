import datetime
import uuid
from typing import Annotated, Literal

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import exceptions as jwt_exceptions
from pydantic import Field
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.constants import JWT_SECRET
from zimfarm_backend.api.routes.http_errors import UnauthorizedError
from zimfarm_backend.api.token import verify_kiwix_access_token
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.db import gen_dbsession, gen_manual_dbsession
from zimfarm_backend.db.models import User
from zimfarm_backend.db.user import get_user_by_id_or_none, get_user_by_idp_sub_or_none

security = HTTPBearer(description="Access Token", auto_error=False)
AuthorizationCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(security)
]


class JWTClaims(BaseModel):
    iss: str
    exp: datetime.datetime
    iat: datetime.datetime
    sub: uuid.UUID = Field(alias="subject")


def get_jwt_claims_or_none(
    authorization: AuthorizationCredentials,
) -> JWTClaims | None:
    """
    Get the JWT claims or None if the user is not authenticated.

    Tries to decode as Zimfarm token first, then as Kiwix token.
    """
    if authorization is None:
        return None
    token = authorization.credentials

    # First, try to decode as Zimfarm token
    try:
        jwt_claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        claims = JWTClaims(**jwt_claims)
        return claims
    except (
        jwt_exceptions.InvalidTokenError,
        jwt_exceptions.PyJWTError,
        PydanticValidationError,
    ):
        # Not a Zimfarm token, try Kiwix token
        pass

    try:
        introspected_token = verify_kiwix_access_token(token)
        return JWTClaims.model_validate(introspected_token)
    except ValueError as exc:
        raise UnauthorizedError("Invalid token") from exc
    except jwt_exceptions.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token has expired.") from exc
    except (jwt_exceptions.InvalidTokenError, jwt_exceptions.PyJWTError) as exc:
        raise UnauthorizedError("Invalid token") from exc
    except Exception as exc:
        raise UnauthorizedError("Unable to verify token") from exc


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
        user = get_user_by_id_or_none(session, user_id=claims.sub)
        if user is None:
            return get_user_by_idp_sub_or_none(session, idp_sub=claims.sub)
        return user

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
