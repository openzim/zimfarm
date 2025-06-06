# pyright: strict, reportGeneralTypeIssues=false
import datetime

import jwt
import paramiko
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from zimfarm_backend.common.constants import (
    JWT_SECRET,
    JWT_TOKEN_EXPIRY_DURATION,
    JWT_TOKEN_ISSUER,
)
from zimfarm_backend.exceptions import PEMPublicKeyLoadError


def generate_access_token(user_id: str) -> str:
    """Generate a JWT access token for the given user ID with configured expiry."""

    issue_time = datetime.datetime.now(datetime.UTC)
    expire_time = issue_time + datetime.timedelta(seconds=JWT_TOKEN_EXPIRY_DURATION)
    payload = {
        "iss": JWT_TOKEN_ISSUER,  # issuer
        "exp": expire_time.timestamp(),  # expiration time
        "iat": issue_time.timestamp(),  # issued at
        "subject": user_id,
    }
    return jwt.encode(payload, key=JWT_SECRET, algorithm="HS256")


def verify_signed_message(public_key: bytes, signature: bytes, message: bytes) -> bool:
    """Verify if a message was signed with the corresponding private key."""
    try:
        pem_public_key = serialization.load_pem_public_key(public_key)
    except Exception as exc:
        raise PEMPublicKeyLoadError("Unable to load public key") from exc

    try:
        pem_public_key.verify(  # pyright: ignore
            signature,
            message,
            padding.PSS(  # pyright: ignore
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),  # pyright: ignore
        )
    except InvalidSignature:
        return False
    return True


def sign_message(private_key: RSAPrivateKey, message: bytes) -> bytes:
    """Sign a message using the provided RSA private key with PSS padding and SHA256."""
    # Needed for testing purposes here only
    return private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )


def generate_public_key(private_key: RSAPrivateKey) -> RSAPublicKey:
    """Extract the public key from an RSA private key."""
    return private_key.public_key()


def serialize_public_key(public_key: RSAPublicKey) -> bytes:
    """Convert an RSA public key to PEM format."""
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def get_public_key_fingerprint(public_key: RSAPublicKey) -> str:
    """Compute the SHA256 fingerprint of an RSA public key."""
    return paramiko.RSAKey(
        key=public_key  # pyright: ignore[reportUnknownMemberType, UnknownVariableType]
    ).fingerprint
