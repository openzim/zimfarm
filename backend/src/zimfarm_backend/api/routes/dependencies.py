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

from zimfarm_backend.api.constants import (
    CREATE_NEW_KIWIX_ACCOUNT,
    JWT_SECRET,
)
from zimfarm_backend.api.routes.http_errors import UnauthorizedError
from zimfarm_backend.api.token import verify_kiwix_access_token
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.db import gen_dbsession, gen_manual_dbsession
from zimfarm_backend.db.models import User
from zimfarm_backend.db.user import (
    check_user_permission,
    create_user,
    get_user_by_id_or_none,
    get_user_by_idp_sub_or_none,
)

security = HTTPBearer(description="Access Token", auto_error=False)
AuthorizationCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(security)
]


class JWTClaims(BaseModel):
    iss: str
    exp: datetime.datetime
    iat: datetime.datetime
    sub: uuid.UUID = Field(alias="subject")
    name: str | None = Field(exclude=True, default=None)


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
    except jwt_exceptions.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token has expired.") from exc
    except (jwt_exceptions.InvalidTokenError, jwt_exceptions.PyJWTError) as exc:
        raise UnauthorizedError("Invalid token") from exc
    except ValueError as exc:
        raise UnauthorizedError(exc.args[0]) from exc
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
            user = get_user_by_idp_sub_or_none(session, idp_sub=claims.sub)
            # If this is a kiwix token, we create a new user account
            if user is None and CREATE_NEW_KIWIX_ACCOUNT:
                if not claims.name:
                    raise UnauthorizedError("Token is missing 'profile' scope")
                create_user(
                    session,
                    username=claims.name,
                    role=RoleEnum.VIEWER,
                    idp_sub=claims.sub,
                )
                user = get_user_by_idp_sub_or_none(session, idp_sub=claims.sub)

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
        # If we get here, it means the token was valid but the user being None
        # means their idp_sub or id doesn't exist on the database or they have been
        # marked as deleted.
        if user is None:
            raise UnauthorizedError(
                "This account is not yet authorized on the Zimfarm. "
                "Please contact Zimfarm admins."
            )

        if user.deleted:
            raise UnauthorizedError("This account does not exist on the Zimfarm.")

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
