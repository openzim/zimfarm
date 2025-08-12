# pyright: strict, reportGeneralTypeIssues=false
import datetime
from base64 import encodebytes
from typing import Any

import jwt
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.primitives.asymmetric.ec import (
    EllipticCurvePrivateKey,
    EllipticCurvePublicKey,
)
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes
from cryptography.hazmat.primitives.serialization import (
    SSHPublicKeyTypes,
    load_pem_public_key,
    load_ssh_public_key,
)

from zimfarm_backend.common.constants import (
    JWT_SECRET,
    JWT_TOKEN_EXPIRY_DURATION,
    JWT_TOKEN_ISSUER,
)
from zimfarm_backend.exceptions import PEMPublicKeyLoadError


def generate_access_token(
    *,
    user_id: str,
    username: str,
    issue_time: datetime.datetime,
    email: str | None = None,
    scope: dict[str, Any] | None = None,
) -> str:
    """Generate a JWT access token for the given user ID with configured expiry."""

    expire_time = issue_time + datetime.timedelta(seconds=JWT_TOKEN_EXPIRY_DURATION)
    payload = {
        "iss": JWT_TOKEN_ISSUER,  # issuer
        "exp": expire_time.timestamp(),  # expiration time
        "iat": issue_time.timestamp(),  # issued at
        "subject": user_id,
        "user": {
            "username": username,
            "email": email,
            "scope": scope or {},
        },
    }
    return jwt.encode(payload, key=JWT_SECRET, algorithm="HS256")


def verify_signed_message(public_key: bytes, signature: bytes, message: bytes) -> bool:
    """Verify if a message was signed with the corresponding private key."""

    pem_public_key = load_public_key(public_key)
    if isinstance(pem_public_key, RSAPublicKey):
        return verify_rsa_signed_message(pem_public_key, signature, message)
    else:
        return verify_ecdsa_signed_message(pem_public_key, signature, message)


def sign_message_with_rsa_key(private_key: RSAPrivateKey, message: bytes) -> bytes:
    """Sign a message using the provided RSA private key with PSS padding and SHA256."""
    # Needed for testing purposes and to show the signature algorithm for
    # reverse verification signature
    return private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )


def verify_rsa_signed_message(
    public_key: RSAPublicKey, signature: bytes, message: bytes
) -> bool:
    """Verify a message was signed using the private key of the RSA public key."""
    try:
        public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
    except InvalidSignature:
        return False
    return True


def sign_message_with_ecdsa_key(
    private_key: EllipticCurvePrivateKey, message: bytes
) -> bytes:
    """Sign a message using the provided ECDSA private key."""
    # Needed for testing purposes and to show the signature algorithm for
    # reverse verification.
    return private_key.sign(message, ec.ECDSA(hashes.SHA256()))


def verify_ecdsa_signed_message(
    public_key: EllipticCurvePublicKey, signature: bytes, message: bytes
) -> bool:
    """Verify a message was signed using the private key of the ECDSA public key."""
    try:
        public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        return False
    return True


def serialize_public_key(public_key: RSAPublicKey | EllipticCurvePublicKey) -> bytes:
    """Convert a public key to PEM format."""
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def get_public_key_fingerprint(
    public_key: RSAPublicKey | EllipticCurvePublicKey,
) -> str:
    """Compute the SHA256 fingerprint of a public key."""
    # Modified from: https://github.com/paramiko/paramiko/blob/2af0dd788d8e97dff51212baed2d870abf3b38eb/paramiko/pkey.py#L357-L369
    hashy = serialization.ssh_key_fingerprint(public_key, hashes.SHA256())
    cleaned = encodebytes(hashy).decode("utf8").strip().rstrip("=")
    return f"SHA256:{cleaned}"


def load_public_key(key: bytes) -> RSAPublicKey | EllipticCurvePublicKey:
    """Load SSH public key from bytes.

    Supported formats for SSH public keys are:
    - RSA  (both in OpenSSH and PEM format)
    - ECDSA (both in OpenSSH and PEM format)
    """

    public_key: SSHPublicKeyTypes | PublicKeyTypes | None = None
    try:
        public_key = load_ssh_public_key(key)
    except (ValueError, UnsupportedAlgorithm):
        try:
            public_key = load_pem_public_key(key)
        except (ValueError, UnsupportedAlgorithm):
            pass

    if public_key is None:
        raise PEMPublicKeyLoadError("Unable to load public key")

    if not isinstance(public_key, RSAPublicKey | EllipticCurvePublicKey):
        raise PEMPublicKeyLoadError("Unsupported public key type.")
    return public_key
