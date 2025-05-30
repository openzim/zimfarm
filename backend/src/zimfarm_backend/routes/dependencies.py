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
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import User
from zimfarm_backend.db.user import get_user_by_id
from zimfarm_backend.routes.http_errors import UnauthorizedError

security = HTTPBearer(description="Access Token")
AuthorizationCredentials = Annotated[HTTPAuthorizationCredentials, Depends(security)]


class JWTClaims(BaseModel):
    iss: str
    exp: datetime.datetime
    iat: datetime.datetime
    subject: uuid.UUID


def get_current_user(
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    authorization: AuthorizationCredentials,
) -> User:
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

    # At this point, we know that the JWT is all OK and we can
    # trust the data in it. We extract the user_id from the claims
    try:
        db_user = get_user_by_id(session, user_id=claims.subject)
    except RecordDoesNotExistError as exc:
        raise UnauthorizedError() from exc
    return db_user
