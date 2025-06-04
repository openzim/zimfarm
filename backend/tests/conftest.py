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

from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import (
    Base,
    RequestedTask,
    Schedule,
    ScheduleDuration,
    Sshkey,
    User,
    Worker,
)
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


@pytest.fixture
def worker(dbsession: OrmSession, user: User) -> Worker:
    """Create a worker for testing"""
    worker = Worker(
        name="testworker",
        selfish=False,
        cpu=2,
        memory=1024,
        disk=1024,
        offliners=["mwoffliner", "youtube"],
        platforms={},
        last_seen=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
        last_ip=None,
    )
    worker.user_id = user.id
    dbsession.add(worker)
    dbsession.flush()
    return worker


@pytest.fixture
def schedule(dbsession: OrmSession) -> Schedule:
    """Create a schedule for testing"""
    schedule = Schedule(
        name="testschedule",
        category="wikipedia",
        config={"task_name": "test_task", "flags": {}},
        enabled=True,
        language_code="en",
        language_name_native="English",
        language_name_en="English",
        tags=["test"],
        periodicity="monthly",
        notification=None,
    )
    dbsession.add(schedule)
    dbsession.flush()
    return schedule


@pytest.fixture
def schedule_duration(
    dbsession: OrmSession, schedule: Schedule, worker: Worker
) -> ScheduleDuration:
    """Create a schedule duration for testing"""
    duration = ScheduleDuration(
        default=True,
        value=3600,  # 1 hour
        on=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
    )
    duration.schedule = schedule
    duration.worker = worker
    dbsession.add(duration)
    dbsession.flush()
    return duration


@pytest.fixture
def requested_task(
    dbsession: OrmSession, schedule: Schedule, worker: Worker
) -> RequestedTask:
    """Create a requested task for testing"""
    now = getnow()
    requested_task = RequestedTask(
        status=TaskStatus.requested,
        timestamp={TaskStatus.requested: now},
        events=[{"code": TaskStatus.requested, "timestamp": now}],
        requested_by="testuser",
        priority=0,
        config={
            "task_name": "mwoffliner",
            "resources": {
                "cpu": 1,
                "memory": 512,
                "disk": 512,
            },
        },
        upload={
            "zim": {
                "upload_uri": "test://upload/zim",
                "expiration": 3600,
                "zimcheck": True,
            },
            "logs": {
                "upload_uri": "test://upload/logs",
                "expiration": 3600,
            },
            "artifacts": {
                "upload_uri": "test://upload/artifacts",
                "expiration": 3600,
            },
        },
        notification={},
        updated_at=now,
        original_schedule_name=schedule.name,
    )
    requested_task.schedule = schedule
    requested_task.worker = worker
    dbsession.add(requested_task)
    dbsession.flush()
    return requested_task


# @pytest.fixture
# def set_default_publisher() -> Generator[Callable]:
#     def _set_default_publisher(publisher: str):
#         constants.DEFAULT_PUBLISHER = publisher
#
#     yield _set_default_publisher
#     constants.DEFAULT_PUBLISHER = None  # Reset to default after test
