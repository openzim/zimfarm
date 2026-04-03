from typing import Annotated, Literal

from fastapi import Depends, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import exceptions as jwt_exceptions
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.constants import (
    CREATE_NEW_OAUTH_ACCOUNT,
)
from zimfarm_backend.api.routes.http_errors import ForbiddenError, UnauthorizedError
from zimfarm_backend.api.token import JWTClaims, token_decoder
from zimfarm_backend.common import is_valid_uuid
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.common.schemas.models import AccountUpdateSchema
from zimfarm_backend.db import gen_dbsession, gen_manual_dbsession
from zimfarm_backend.db.account import (
    check_account_permission,
    create_account,
    get_account_by_id_or_none,
    update_account,
)
from zimfarm_backend.db.models import Account

security = HTTPBearer(description="Access Token", auto_error=False)
AuthorizationCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(security)
]


def get_jwt_claims_or_none(
    authorization: AuthorizationCredentials,
) -> JWTClaims | None:
    """
    Get the JWT claims or None if the account is not authenticated.

    Tries to decode as Zimfarm token first, then as Kiwix token.
    """
    if authorization is None:
        return None
    token = authorization.credentials

    try:
        return token_decoder.decode(token)
    except jwt_exceptions.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token has expired.") from exc
    except (jwt_exceptions.InvalidTokenError, jwt_exceptions.PyJWTError) as exc:
        raise UnauthorizedError("Invalid token") from exc
    except ValueError as exc:
        raise UnauthorizedError(exc.args[0]) from exc
    except Exception as exc:
        raise UnauthorizedError("Unable to verify token") from exc


def get_current_account_or_none_with_session(
    session_type: Literal["auto", "manual"] = "auto",
):
    def _get_current_account_or_none(
        claims: Annotated[JWTClaims | None, Depends(get_jwt_claims_or_none)],
        session: Annotated[
            OrmSession,
            Depends(gen_dbsession if session_type == "auto" else gen_manual_dbsession),
        ],
    ) -> Account | None:
        if claims is None:
            return None
        account = get_account_by_id_or_none(
            session, account_id=claims.sub, fetch_ssh_keys=True
        )
        # If this is a kiwix token, we create a new account account
        if account is None and CREATE_NEW_OAUTH_ACCOUNT:
            if not claims.name:
                raise UnauthorizedError("Token is missing 'profile' scope")
            create_account(
                session,
                display_name=claims.name,
                role=RoleEnum.VIEWER,
                idp_sub=claims.sub,
            )
            account = get_account_by_id_or_none(
                session, account_id=claims.sub, fetch_ssh_keys=True
            )

        # if token contains a "name" attribute and display_name is different, update it
        if account and claims.name and claims.name != account.display_name:
            update_account(
                session,
                account_id=account.id,
                request=AccountUpdateSchema(display_name=claims.name),
            )

        return account

    return _get_current_account_or_none


def get_current_account_with_session(
    session_type: Literal["auto", "manual"] = "auto",
):
    def _get_current_account(
        account: Annotated[
            Account | None,
            Depends(
                get_current_account_or_none_with_session(session_type=session_type)
            ),
        ],
    ) -> Account:
        # If we get here, it means the token was valid but the account being None
        # means their idp_sub or id doesn't exist on the database or they have been
        # marked as deleted.
        if account is None:
            raise UnauthorizedError(
                "This account is not yet authorized on the Zimfarm. "
                "Please contact Zimfarm admins."
            )

        if account.deleted:
            raise UnauthorizedError("This account does not exist on the Zimfarm.")

        return account

    return _get_current_account


# Convenience functions for common cases
get_current_account_or_none = get_current_account_or_none_with_session(
    session_type="auto"
)
get_current_account = get_current_account_with_session(session_type="auto")


def require_permission(*, namespace: str, name: str):
    """
    checks if the current account has a specific permission.
    """

    def _check_permission(
        current_account: Annotated[Account, Depends(get_current_account)],
    ) -> Account:
        if not check_account_permission(
            current_account, namespace=namespace, name=name
        ):
            raise UnauthorizedError(
                "You do not have permission to perform this action. "
            )
        return current_account

    return _check_permission


def require_permission_if_not_self(namespace: str, name: str):
    """Ensure that an account has permission to access another account's resource."""

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
