import abc
import base64
import binascii
import datetime
import uuid
from typing import NamedTuple

import jwt
from jwt import PyJWKClient
from jwt import exceptions as jwt_exceptions
from pydantic import Field
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend import logger
from zimfarm_backend.api.constants import (
    AUTH_MODES,
    JWT_SECRET,
    JWT_TOKEN_EXPIRY_DURATION,
    JWT_TOKEN_ISSUER,
    OAUTH_ISSUER,
    OAUTH_JWKS_URI,
    OAUTH_OIDC_CLIENT_ID,
    OAUTH_OIDC_LOGIN_REQUIRE_2FA,
    OAUTH_SESSION_AUDIENCE_ID,
    OAUTH_SESSION_LOGIN_REQUIRE_2FA,
)
from zimfarm_backend.common import getnow
from zimfarm_backend.common.constants import MESSAGE_VALIDITY_DURATION
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.worker import get_worker
from zimfarm_backend.exceptions import PublicKeyLoadError
from zimfarm_backend.utils.cryptography import verify_signed_message


class SSHTokenParts(NamedTuple):
    worker_name: str
    timestamp: str
    signature: bytes


class JWTClaims(BaseModel):
    iss: str
    exp: datetime.datetime
    iat: datetime.datetime
    sub: uuid.UUID = Field(alias="subject")
    name: str | None = Field(exclude=True, default=None)


class TokenDecoder(abc.ABC):
    """Abstract base class for token decoders."""

    @abc.abstractmethod
    def decode(self, token: str, session: OrmSession | None = None) -> JWTClaims:
        """
        Decode and validate a token.
        """
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """
        Human-readable identifier of the decoder.
        """
        pass

    @abc.abstractmethod
    def can_decode(self, token: str) -> bool:
        """
        Check if this decoder can potentially decode the given token.
        """
        pass


class SshTokenDecoder(TokenDecoder):
    """Decoder for SSH bearer tokens"""

    def decode(self, token: str, session: OrmSession | None = None) -> JWTClaims:
        """
        Decode and validate an ssh authentication message.
        """
        worker_name, timestamp, signature = self._extract_token_parts(token)

        exp = datetime.datetime.fromisoformat(timestamp) + datetime.timedelta(
            seconds=MESSAGE_VALIDITY_DURATION
        )
        if getnow() > exp:
            raise ValueError(
                "Difference between message time and server time is "
                f"greater than {MESSAGE_VALIDITY_DURATION}s"
            )

        if session is None:
            raise ValueError("OrmSession is required to decode SSH bearer tokens.")

        try:
            db_worker = get_worker(session, worker_name=worker_name)
        except RecordDoesNotExistError as exc:
            raise ValueError(f"Worker {worker_name} does not exist.") from exc

        authenticated = False
        # Verify signature with workers' public keys
        for ssh_key in db_worker.ssh_keys:
            try:
                if verify_signed_message(
                    bytes(ssh_key.key, encoding="ascii"),
                    signature,
                    bytes(f"{worker_name}.{timestamp}", encoding="ascii"),
                ):
                    authenticated = True
                    break
            except PublicKeyLoadError as exc:
                logger.exception("error while verifying message using public key")
                raise ValueError("Unable to load public_key") from exc

        if not authenticated:
            raise ValueError("Could not find matching key for signature.")

        return JWTClaims(
            iss="zimfarm-worker",
            exp=exp,
            iat=datetime.datetime.fromisoformat(timestamp),
            # use the account id so route permission checks are done against the worker
            # account
            subject=db_worker.account_id,
        )

    def _extract_token_parts(self, token: str) -> SSHTokenParts:
        """Extract SSH token parts"""
        try:
            worker_name, timestamp, signature = token.split(".", 2)
            datetime.datetime.fromisoformat(timestamp)
        except ValueError as exc:
            raise ValueError("Invalid message format.") from exc

        try:
            signature = base64.standard_b64decode(signature)
        except binascii.Error as exc:
            raise ValueError("Invalid signature format (not base64)") from exc

        return SSHTokenParts(
            worker_name=worker_name, timestamp=timestamp, signature=signature
        )

    @property
    def name(self) -> str:
        return "ssh"

    def can_decode(self, token: str) -> bool:
        # First few checks that don't require should fail early  if this is not
        # an SSH bearer token.
        try:
            self._extract_token_parts(token)
        except Exception:
            return False
        return True


class LocalTokenDecoder(TokenDecoder):
    """Decoder for local Zimfarm JWT tokens."""

    def __init__(self, secret: str = JWT_SECRET, algorithm: str = "HS256"):
        self.secret = secret
        self.algorithm = algorithm

    def decode(
        self,
        token: str,
        session: OrmSession | None = None,  # noqa: ARG002
    ) -> JWTClaims:
        """
        Decode and validate a local Zimfarm token.
        """
        jwt_claims = jwt.decode(token, self.secret, algorithms=[self.algorithm])
        return JWTClaims(**jwt_claims)

    @property
    def name(self) -> str:
        return "local"

    def can_decode(self, token: str) -> bool:
        if "local" not in AUTH_MODES:
            return False
        try:
            payload = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                    "verify_aud": False,
                    "verify_iss": False,
                },
            )
        except Exception:
            return False

        if payload.get("iss") != JWT_TOKEN_ISSUER:
            return False
        return True


class OAuthOIDCTokenDecoder(TokenDecoder):
    """Decoder for OAuth OIDC JWT tokens."""

    def __init__(self):
        """Initialize OAuth token decoder."""
        self._jwks_client = PyJWKClient(
            OAUTH_JWKS_URI,
            cache_keys=True,
            headers={"User-Agent": "PyJWT/2.11.0"},
        )

    def decode(
        self,
        token: str,
        session: OrmSession | None = None,  # noqa: ARG002
    ) -> JWTClaims:
        """
        Decode and validate an OAuth OIDC token.
        """
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)
        decoded_token = jwt.decode(
            token,
            signing_key.key,
            algorithms=[signing_key.algorithm_name],
            issuer=OAUTH_ISSUER,
            audience=OAUTH_OIDC_CLIENT_ID,
            options={
                "require": ["exp", "iat", "iss", "sub", "aud"],
            },
        )

        if (
            client_id := decoded_token.get("client_id")
        ) and client_id != decoded_token.get("sub"):
            raise ValueError("Oauth client ID does not match.")

        # Check for 2FA requirement only if client_id is not present in the token
        # as those come from oauth2 clients and not real accounts.
        # Ensure the account logged in with two authentication factors. As per Ory docs,
        # "password", "code"  and "oidc" are categorized as first methods of login while
        # "totp", "webauthn" and "lookup_secret" are second authentication methods
        # https://www.ory.com/docs/kratos/mfa/overview#authenticator-assurance-level-aal
        amr = set(decoded_token.get("amr", []))
        if (
            not decoded_token.get("client_id")
            and OAUTH_OIDC_LOGIN_REQUIRE_2FA
            and not (
                {"password", "oidc", "code"} & amr
                and {"webauthn", "lookup_secrets", "totp"} & amr
            )
        ):
            raise ValueError(
                "2FA authentication is mandatory on Zimfarm but it looks like you only "
                "have one setup on Ory. Please, configure a second one on Ory at "
                f"{OAUTH_ISSUER}/settings"
            )
        return JWTClaims.model_validate(decoded_token)

    @property
    def name(self) -> str:
        return "oauth-oidc"

    def can_decode(self, token: str) -> bool:
        if "oauth-oidc" not in AUTH_MODES:
            return False
        try:
            payload = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                    "verify_aud": False,
                    "verify_iss": False,
                },
            )
        except Exception:
            return False

        if payload.get(
            "iss"
        ) != OAUTH_ISSUER or OAUTH_OIDC_CLIENT_ID not in payload.get("aud", []):
            return False

        return True


class OAuthSessionTokenDecoder(TokenDecoder):
    """Decoder for OAuth Session JWT tokens."""

    def __init__(self):
        """Initialize OAuth token decoder."""
        self._jwks_client = PyJWKClient(
            OAUTH_JWKS_URI,
            cache_keys=True,
            headers={"User-Agent": "PyJWT/2.11.0"},
        )

    def decode(
        self,
        token: str,
        session: OrmSession | None = None,  # noqa: ARG002
    ) -> JWTClaims:
        """
        Decode and validate an OAuth OIDC token.
        """
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)

        decoded_token = jwt.decode(
            token,
            signing_key.key,
            algorithms=[signing_key.algorithm_name],
            issuer=OAUTH_ISSUER,
            audience=OAUTH_SESSION_AUDIENCE_ID,
            options={
                "require": ["exp", "iat", "iss", "sub", "aud"],
            },
        )

        if (
            client_id := decoded_token.get("client_id")
        ) and client_id != decoded_token.get("sub"):
            raise ValueError("Oauth client ID does not match.")

        # Check for 2FA requirement only if client_id is not present in the token
        # as those come from oauth2 clients and not real accounts
        if (
            not decoded_token.get("client_id")
            and OAUTH_SESSION_LOGIN_REQUIRE_2FA
            and decoded_token.get("aal") != "aal2"
        ):
            raise ValueError(
                "2FA authentication is mandatory on Zimfarm but it looks like you only "
                "have one setup on Ory. Please, configure a second one on Ory at "
                f"{OAUTH_ISSUER}/settings"
            )
        return JWTClaims.model_validate(decoded_token)

    @property
    def name(self) -> str:
        return "oauth-session"

    def can_decode(self, token: str) -> bool:
        if "oauth-session" not in AUTH_MODES:
            return False
        try:
            payload = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                    "verify_aud": False,
                    "verify_iss": False,
                },
            )
        except Exception:
            return False

        if payload.get(
            "iss"
        ) != OAUTH_ISSUER or OAUTH_SESSION_AUDIENCE_ID not in payload.get("aud", []):
            return False
        return True


class TokenDecoderChain:
    """Chain of responsibility for token decoders."""

    def __init__(self, decoders: list[TokenDecoder]):
        """
        Initialize decoder chain.
        """
        self.decoders = decoders

    def decode(self, token: str, session: OrmSession) -> JWTClaims:
        """
        Try to decode token using each decoder in order.
        """
        exc_cls: Exception | None = None
        decoders = [decoder for decoder in self.decoders if decoder.can_decode(token)]
        if not decoders:
            raise ValueError("No decoders can decode token.")

        if len(decoders) > 1:
            logger.warning(
                "Multiple token decoders detected. Set configuration values to match "
                "only one token decoder to avoid overwriting exception messages."
            )

        logger.debug(f"{len(decoders)} decoder(s) can decode token")

        for decoder in decoders:
            try:
                logger.debug(f"{decoder.name}-decoder: attempting to decode token.")
                claims = decoder.decode(token, session)
            except (
                jwt_exceptions.PyJWTError,
                PydanticValidationError,
                Exception,
            ) as exc:
                logger.debug(f"{decoder.name}-decoder: unable to decode token: {exc!s}")
                exc_cls = exc
            else:
                logger.debug(f"{decoder.name}-decoder: decoded token successfully.")
                return claims

        if exc_cls:
            raise exc_cls

        raise ValueError("Invalid token")


token_decoder = TokenDecoderChain(
    decoders=[
        SshTokenDecoder(),
        LocalTokenDecoder(),
        OAuthOIDCTokenDecoder(),
        OAuthSessionTokenDecoder(),
    ]
)


def generate_access_token(
    *,
    account_id: str,
    issue_time: datetime.datetime,
) -> str:
    """Generate a JWT access token for the given account ID with configured expiry."""

    expire_time = issue_time + datetime.timedelta(seconds=JWT_TOKEN_EXPIRY_DURATION)
    payload = {
        "iss": JWT_TOKEN_ISSUER,  # issuer
        "exp": expire_time.timestamp(),  # expiration time
        "iat": issue_time.timestamp(),  # issued at
        "subject": account_id,
    }
    return jwt.encode(payload, key=JWT_SECRET, algorithm="HS256")
