import base64
import datetime
from collections.abc import Generator
from typing import cast

import paramiko
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from faker import Faker
from pytest import FixtureRequest, Mark
from sqlalchemy.orm import Session as OrmSession
from werkzeug.security import generate_password_hash

from zimfarm_backend.common.roles import ROLES, RoleEnum
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import Base, Sshkey, User
from zimfarm_backend.utils.token import generate_access_token, sign_message


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
def data_gen(faker: Faker) -> Faker:
    """Sets up faker to generate random data for testing."""
    # Setting a fixed seed ensures that Faker generates the same fake data
    # on every test run. This makes tests deterministic and reproducible,
    # so failures are easier to debug and tests are more reliable.
    # Other test submodules can choose a new seed value.
    faker.seed_instance(123)

    return faker


@pytest.fixture
def private_key() -> RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def public_key(private_key: RSAPrivateKey) -> RSAPublicKey:
    return private_key.public_key()


@pytest.fixture
def public_key_data(private_key: RSAPrivateKey) -> bytes:
    """Serialize public key using PEM format."""
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


@pytest.fixture
def auth_message(user: User) -> str:
    return f"{user.username}:{datetime.datetime.now(datetime.UTC).isoformat()}"


@pytest.fixture
def x_sshauth_signature(private_key: RSAPrivateKey, auth_message: str) -> str:
    """Sign a message using RSA private key and encode it in base64"""
    signature = sign_message(private_key, bytes(auth_message, encoding="ascii"))
    return base64.b64encode(signature).decode()


@pytest.fixture
def access_token(user: User) -> str:
    return generate_access_token(str(user.id))


@pytest.fixture
def users(
    dbsession: OrmSession,
    public_key: RSAPublicKey,
    public_key_data: bytes,
    data_gen: Faker,
    request: FixtureRequest,
) -> list[User]:
    """Adds users to the database using the num_users mark."""
    mark = cast(
        Mark,
        request.node.get_closest_marker(  # pyright: ignore[reportUnknownMemberType]
            "num_users"
        ),
    )
    if mark and len(mark.args) > 0:
        num_users = int(mark.args[0])
    else:
        num_users = 10

    if mark:
        permissions = mark.kwargs.get("permission", RoleEnum.ADMIN)
    else:
        permissions = RoleEnum.ADMIN

    users: list[User] = []

    for _ in range(num_users):
        pubkey_pkcs8 = public_key_data.decode("ascii")

        user = User(
            username=data_gen.first_name(),
            password_hash=generate_password_hash("testpassword"),
            email=data_gen.safe_email(),
            scope=ROLES[permissions],
        )
        dbsession.add(user)

        key = Sshkey(
            name=data_gen.word(),
            key=public_key_data.decode("ascii"),
            fingerprint=paramiko.RSAKey(key=public_key).fingerprint,  # type: ignore
            type="RSA",
            added=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
            pkcs8_key=pubkey_pkcs8,
        )
        key.user = user

        dbsession.add(key)
        dbsession.flush()

        users.append(user)

    return users


# @pytest.fixture
# def set_default_publisher() -> Generator[Callable]:
# @pytest.fixture
# def set_default_publisher() -> Generator[Callable]:
#     def _set_default_publisher(publisher: str):
#         constants.DEFAULT_PUBLISHER = publisher
#
#     yield _set_default_publisher
#     constants.DEFAULT_PUBLISHER = None  # Reset to default after test
