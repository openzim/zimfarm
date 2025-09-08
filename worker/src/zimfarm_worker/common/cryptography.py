import base64
from base64 import encodebytes
from dataclasses import dataclass
from pathlib import Path

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.primitives.asymmetric.ec import (
    EllipticCurvePrivateKey,
    EllipticCurvePublicKey,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.asymmetric.types import (
    PrivateKeyTypes,
)
from cryptography.hazmat.primitives.serialization import (
    SSHPrivateKeyTypes,
)

from zimfarm_worker.common import getnow


@dataclass
class AuthMessage:
    """An authentication message for a worker"""

    body: str
    signature: str


# Majority of these functions are copied from zimfarm_backend which also contains the
# reverse logic for verifying messages. Need to do so to ensure we are signing with the
# same hash algorithms the backend expects.


def sign_message_with_rsa_key(private_key: RSAPrivateKey, message: bytes) -> bytes:
    """Sign a message using the provided RSA private key with PSS padding and SHA256."""
    return private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )


def sign_message_with_ecdsa_key(
    private_key: EllipticCurvePrivateKey, message: bytes
) -> bytes:
    """Sign a message using the provided ECDSA private key."""
    return private_key.sign(message, ec.ECDSA(hashes.SHA256()))


def sign_message_with_ed25519_key(
    private_key: Ed25519PrivateKey, message: bytes
) -> bytes:
    """Sign a message using the provided Ed25519 private key."""
    return private_key.sign(message)


def load_private_key_from_path(
    private_key_fpath: Path,
) -> RSAPrivateKey | EllipticCurvePrivateKey | Ed25519PrivateKey:
    """Load a private key from a file path

    Attempts to load the private key in SSH or PEM format.
    """

    content = private_key_fpath.read_bytes()
    private_key: SSHPrivateKeyTypes | PrivateKeyTypes | None = None
    try:
        private_key = serialization.load_ssh_private_key(content, password=None)
    except (ValueError, UnsupportedAlgorithm):
        try:
            private_key = serialization.load_pem_private_key(content, password=None)
        except (ValueError, UnsupportedAlgorithm):
            pass

    if private_key is None:
        raise ValueError("Unable to load private key")

    if not isinstance(
        private_key, RSAPrivateKey | EllipticCurvePrivateKey | Ed25519PrivateKey
    ):
        raise ValueError("Key is not an RSA private key")
    return private_key


def get_public_key_fingerprint(
    public_key: RSAPublicKey | EllipticCurvePublicKey | Ed25519PublicKey,
) -> str:
    """Compute the SHA256 fingerprint of a public key."""
    # Modified from: https://github.com/paramiko/paramiko/blob/2af0dd788d8e97dff51212baed2d870abf3b38eb/paramiko/pkey.py#L357-L369
    hashy = serialization.ssh_key_fingerprint(public_key, hashes.SHA256())
    cleaned = encodebytes(hashy).decode("utf8").strip().rstrip("=")
    return f"SHA256:{cleaned}"


def get_signature(
    message: bytes,
    private_key: RSAPrivateKey | EllipticCurvePrivateKey | Ed25519PrivateKey,
) -> str:
    """Get a base64 encoded signature for a message using the private key"""
    match private_key:
        case RSAPrivateKey():
            signature = sign_message_with_rsa_key(private_key, message)
        case EllipticCurvePrivateKey():
            signature = sign_message_with_ecdsa_key(private_key, message)
        case Ed25519PrivateKey():
            signature = sign_message_with_ed25519_key(private_key, message)
    return base64.b64encode(signature).decode()


def generate_auth_message(
    worker_id: str,
    private_key: RSAPrivateKey | EllipticCurvePrivateKey | Ed25519PrivateKey,
) -> AuthMessage:
    """Generate an authentication message for a worker"""
    body = f"{worker_id}:{getnow().isoformat()}"
    return AuthMessage(
        body=body, signature=get_signature(bytes(body, encoding="ascii"), private_key)
    )
