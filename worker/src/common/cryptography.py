import base64
import datetime
from dataclasses import dataclass
from pathlib import Path

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.asymmetric.types import (
    PrivateKeyTypes,
)
from cryptography.hazmat.primitives.serialization import SSHPrivateKeyTypes


@dataclass
class AuthMessage:
    """An authentication message for a worker"""

    body: str
    signature: str


def load_private_key_from_path(private_key_fpath: Path) -> RSAPrivateKey:
    """Load a private key from a file path

    Attempts to load the private key in SSH or PEM format.
    """

    private_key: SSHPrivateKeyTypes | PrivateKeyTypes | None = None
    try:
        private_key = serialization.load_ssh_private_key(
            private_key_fpath.read_bytes(), password=None
        )
    except (ValueError, UnsupportedAlgorithm):
        try:
            private_key = serialization.load_pem_private_key(
                private_key_fpath.read_bytes(), password=None
            )
        except (ValueError, UnsupportedAlgorithm):
            pass

    if private_key is None:
        raise ValueError("Unable to load private key")

    if not isinstance(private_key, RSAPrivateKey):
        raise ValueError("Key is not an RSA private key")
    return private_key


def get_signature(message: str, private_key: RSAPrivateKey) -> str:
    """Get a signature for a message using the private key"""
    signed_message = private_key.sign(
        bytes(message, encoding="ascii"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signed_message).decode()


def generate_auth_message(worker_id: str, private_key: RSAPrivateKey) -> AuthMessage:
    """Generate an authentication message for a worker"""
    body = f"{worker_id}:{datetime.datetime.now(datetime.UTC).isoformat()}"
    return AuthMessage(body=body, signature=get_signature(body, private_key))
