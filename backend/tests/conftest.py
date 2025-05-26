import base64
import datetime
from collections.abc import Generator

import paramiko
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from sqlalchemy.orm import Session as OrmSession
from werkzeug.security import generate_password_hash

from zimfarm_backend.db import Session
from zimfarm_backend.db.models import Base, Sshkey, User
from zimfarm_backend.utils.token import sign_message


@pytest.fixture
def dbsession() -> Generator[OrmSession]:
    with Session.begin() as session:
        # Ensure we are starting with an empty database
        engine = session.get_bind()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        yield session
        session.rollback()


@pytest.fixture
def private_key() -> RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def public_key_data(private_key: RSAPrivateKey) -> bytes:
    """Serialize public key using PEM format."""
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


@pytest.fixture
def user(public_key_data: bytes, dbsession: OrmSession) -> User:
    """Create a user for testing"""

    public_key = serialization.load_pem_public_key(  # pyright: ignore[reportReturnType]
        public_key_data
    )
    pubkey_pkcs8 = public_key.public_bytes(
        serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode(encoding="ascii")

    user = User(
        username="testuser",
        password_hash=generate_password_hash("testpassword"),
        email="testuser@example.com",
        scope={"test": "test"},
    )
    dbsession.add(user)

    key = Sshkey(
        name="testsshkey",
        key=public_key_data.decode("ascii"),
        fingerprint=paramiko.RSAKey(key=public_key).fingerprint,  # type: ignore
        type="RSA",
        added=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
        pkcs8_key=pubkey_pkcs8,
    )
    key.user = user

    dbsession.add(key)
    dbsession.flush()
    return user


@pytest.fixture
def auth_message(user: User) -> str:
    return f"{user.username}:{datetime.datetime.now(datetime.UTC).isoformat()}"


@pytest.fixture
def x_sshauth_signature(private_key: RSAPrivateKey, auth_message: str) -> str:
    """Sign a message using RSA private key and encode it in base64"""
    signature = sign_message(private_key, bytes(auth_message, encoding="ascii"))
    return base64.b64encode(signature).decode()


# @pytest.fixture
# def set_default_publisher() -> Generator[Callable]:
#     def _set_default_publisher(publisher: str):
#         constants.DEFAULT_PUBLISHER = publisher
#
#     yield _set_default_publisher
#     constants.DEFAULT_PUBLISHER = None  # Reset to default after test
