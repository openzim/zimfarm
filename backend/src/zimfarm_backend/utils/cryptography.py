# pyright: strict, reportGeneralTypeIssues=false
from base64 import encodebytes

from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
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
from cryptography.hazmat.primitives.serialization import (
    SSHPublicKeyTypes,
    load_ssh_public_key,
)

from zimfarm_backend.exceptions import PublicKeyLoadError


def verify_signed_message(public_key: bytes, signature: bytes, message: bytes) -> bool:
    """Verify if a message was signed with the corresponding private key."""

    pem_public_key = load_public_key(public_key)
    match pem_public_key:
        case RSAPublicKey():
            return verify_rsa_signed_message(pem_public_key, signature, message)
        case Ed25519PublicKey():
            return verify_ed25519_signed_message(pem_public_key, signature, message)
        case EllipticCurvePublicKey():
            return verify_ecdsa_signed_message(pem_public_key, signature, message)
        case _:
            raise ValueError("Unsupported key type")


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


def sign_message_with_ed25519_key(
    private_key: Ed25519PrivateKey, message: bytes
) -> bytes:
    """Sign a message using the provided Ed25519 private key."""
    # Needed for testing purposes and to show the signature algorithm for
    # reverse verification.
    return private_key.sign(message)


def verify_ed25519_signed_message(
    public_key: Ed25519PublicKey, signature: bytes, message: bytes
) -> bool:
    """Verify a message was signed using the private key of the Ed25519 public key."""
    try:
        public_key.verify(signature, message)
    except InvalidSignature:
        return False
    return True


def serialize_public_key(
    public_key: RSAPublicKey | EllipticCurvePublicKey | Ed25519PublicKey,
) -> bytes:
    """Convert a public key to PEM format."""
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def get_public_key_fingerprint(
    public_key: RSAPublicKey | EllipticCurvePublicKey | Ed25519PublicKey,
) -> str:
    """Compute the SHA256 fingerprint of a public key."""
    # Modified from: https://github.com/paramiko/paramiko/blob/2af0dd788d8e97dff51212baed2d870abf3b38eb/paramiko/pkey.py#L357-L369
    hashy = serialization.ssh_key_fingerprint(public_key, hashes.SHA256())
    cleaned = encodebytes(hashy).decode("utf8").strip().rstrip("=")
    return f"SHA256:{cleaned}"


def load_public_key(
    key: bytes,
) -> RSAPublicKey | EllipticCurvePublicKey | Ed25519PublicKey:
    """Load SSH public key from bytes.

    Supported formats for SSH public keys are:
    - RSA  (OpenSSH format)
    - ECDSA (OpenSSH format)
    - Ed25519 (OpenSSH format)
    """

    public_key: SSHPublicKeyTypes | None = None
    try:
        public_key = load_ssh_public_key(key)
    except (ValueError, UnsupportedAlgorithm):
        pass

    if public_key is None:
        raise PublicKeyLoadError("Unable to load public key")

    if not isinstance(
        public_key, RSAPublicKey | EllipticCurvePublicKey | Ed25519PublicKey
    ):
        raise PublicKeyLoadError("Unsupported public key type.")
    return public_key


def get_public_key_type(key: SSHPublicKeyTypes):
    match key:
        case RSAPublicKey():
            return "RSA"
        case EllipticCurvePublicKey():
            return "ECDSA"
        case Ed25519PublicKey():
            return "ED25519"
        case _:
            raise ValueError("Unsupported key type.")
