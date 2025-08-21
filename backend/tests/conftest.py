import base64
import datetime
from collections.abc import Callable, Generator
from ipaddress import IPv4Address
from typing import Any, cast

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from faker import Faker
from faker.providers import DynamicProvider
from pydantic import AnyUrl, SecretStr
from pytest import FixtureRequest, Mark
from sqlalchemy.orm import Session as OrmSession
from werkzeug.security import generate_password_hash

from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import Platform, TaskStatus, WarehousePath
from zimfarm_backend.common.roles import ROLES, RoleEnum
from zimfarm_backend.common.schemas.models import (
    DockerImageName,
    DockerImageSchema,
    LanguageSchema,
    ResourcesSchema,
    ScheduleConfigSchema,
)
from zimfarm_backend.common.schemas.offliners import MWOfflinerFlagsSchema
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import (
    Base,
    RequestedTask,
    Schedule,
    ScheduleDuration,
    Sshkey,
    Task,
    User,
    Worker,
)
from zimfarm_backend.db.schedule import DEFAULT_SCHEDULE_DURATION, get_schedule_or_none
from zimfarm_backend.utils.offliners import expanded_config
from zimfarm_backend.utils.timestamp import get_timestamp_for_status
from zimfarm_backend.utils.token import (
    generate_access_token,
    get_public_key_fingerprint,
    sign_message_with_rsa_key,
)


@pytest.fixture
def dbsession() -> Generator[OrmSession]:
    session = Session()
    # Ensure we are starting with an empty database
    engine = session.get_bind()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def data_gen(faker: Faker) -> Faker:
    """Sets up faker to generate random data for testing.

    Registers task_status as a provider.
    data_gen.task_status() returns a task status.
    All other providers from Faker can be used accordingly.
    """
    task_status_provider = DynamicProvider(
        provider_name="task_status",
        elements=list(TaskStatus),
    )
    faker.add_provider(task_status_provider)

    # Setting a fixed seed ensures that Faker generates the same fake data
    # on every test run. This makes tests deterministic and reproducible,
    # so failures are easier to debug and tests are more reliable.
    # Other test submodules can choose a new seed value.
    faker.seed_instance(123)

    return faker


@pytest.fixture
def rsa_private_key() -> RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def rsa_public_key(rsa_private_key: RSAPrivateKey) -> RSAPublicKey:
    return rsa_private_key.public_key()


@pytest.fixture
def rsa_public_key_data(rsa_private_key: RSAPrivateKey) -> bytes:
    """Serialize public key using PEM format."""
    return rsa_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


@pytest.fixture
def auth_message(user: User) -> str:
    return f"{user.username}:{getnow().isoformat()}"


@pytest.fixture
def rsa_x_sshauth_signature(rsa_private_key: RSAPrivateKey, auth_message: str) -> str:
    """Sign a message using RSA private key and encode it in base64"""
    signature = sign_message_with_rsa_key(
        rsa_private_key, bytes(auth_message, encoding="ascii")
    )
    return base64.b64encode(signature).decode()


@pytest.fixture
def access_token(user: User) -> str:
    return generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )


@pytest.fixture
def create_user(
    dbsession: OrmSession,
    rsa_public_key: RSAPublicKey,
    rsa_public_key_data: bytes,
    data_gen: Faker,
) -> Callable[..., User]:
    def _create_user(*, permission: RoleEnum = RoleEnum.ADMIN):
        pubkey_pkcs8 = rsa_public_key_data.decode("ascii")

        user = User(
            username=data_gen.first_name(),
            password_hash=generate_password_hash("testpassword"),
            email=data_gen.safe_email(),
            scope=ROLES[permission],
        )
        dbsession.add(user)

        key = Sshkey(
            name=data_gen.word(),
            key=rsa_public_key_data.decode("ascii"),
            fingerprint=get_public_key_fingerprint(rsa_public_key),
            type="RSA",
            added=getnow(),
            pkcs8_key=pubkey_pkcs8,
        )
        key.user = user

        dbsession.add(key)
        dbsession.flush()

        return user

    return _create_user


@pytest.fixture
def users(
    create_user: Callable[..., User],
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
        permission = mark.kwargs.get("permission", RoleEnum.ADMIN)
    else:
        permission = RoleEnum.ADMIN

    users: list[User] = []

    for _ in range(num_users):
        user = create_user(permission=permission)
        users.append(user)

    return users


@pytest.fixture
def user(create_user: Callable[..., User]):
    return create_user()


@pytest.fixture
def create_worker(dbsession: OrmSession, user: User) -> Callable[..., Worker]:
    def _create_worker(
        *,
        name: str = "testworker",
        cpu: int = 2,
        memory: int = 1024,
        disk: int = 1024,
        offliners: list[str] | None = None,
        platforms: dict[str, int] | None = None,
        last_seen: datetime.datetime | None = None,
        last_ip: IPv4Address | None = None,
        deleted: bool = False,
    ) -> Worker:
        _platforms = platforms or {
            Platform.wikimedia: 100,
            Platform.youtube: 100,
        }

        _ip = last_ip or IPv4Address("127.0.0.1")

        worker = Worker(
            name=name,
            selfish=False,
            cpu=cpu,
            memory=memory,
            disk=disk,
            offliners=offliners or ["mwoffliner", "youtube"],
            platforms=_platforms,
            last_seen=last_seen or getnow(),
            last_ip=_ip,
            deleted=deleted,
        )
        worker.user_id = user.id
        dbsession.add(worker)
        dbsession.flush()
        return worker

    return _create_worker


@pytest.fixture
def worker(create_worker: Callable[..., Worker]) -> Worker:
    """Create a worker for testing"""
    return create_worker()


@pytest.fixture
def schedule_duration(
    dbsession: OrmSession, schedule: Schedule, worker: Worker
) -> ScheduleDuration:
    """Create a schedule duration for testing"""
    duration = ScheduleDuration(
        default=True,
        value=3600,  # 1 hour
        on=getnow(),
    )
    duration.schedule = schedule
    duration.worker = worker
    dbsession.add(duration)
    dbsession.flush()
    return duration


@pytest.fixture
def language() -> LanguageSchema:
    return LanguageSchema(
        code="eng",
        name_en="English",
        name_native="English",
    )


@pytest.fixture
def create_schedule_config() -> Callable[..., ScheduleConfigSchema]:
    def _create_schedule_config(
        cpu: int = 2, memory: int = 2**30, disk: int = 2**30
    ) -> ScheduleConfigSchema:
        return ScheduleConfigSchema(
            warehouse_path=WarehousePath.videos,
            image=DockerImageSchema(
                name=DockerImageName.mwoffliner,
                tag="latest",
            ),
            resources=ResourcesSchema(
                cpu=cpu,
                memory=memory,
                disk=disk,
            ),
            offliner=MWOfflinerFlagsSchema(
                offliner_id="mwoffliner",
                mwUrl=AnyUrl("https://en.wikipedia.org"),
                adminEmail="test@kiwix.org",
                mwPassword=SecretStr("test-password"),
            ),
            platform=Platform.wikimedia,
            monitor=True,
        )

    return _create_schedule_config


@pytest.fixture
def schedule_config(
    create_schedule_config: Callable[..., ScheduleConfigSchema],
) -> ScheduleConfigSchema:
    return create_schedule_config(cpu=1, memory=2**30, disk=2**30)


@pytest.fixture
def create_schedule(
    dbsession: OrmSession,
    schedule_config: ScheduleConfigSchema,
    language: LanguageSchema,
):
    _language = language
    _schedule_config = schedule_config

    def _create_schedule(
        *,
        name: str = "testschedule",
        category: str = "wikipedia",
        periodicity: str = "monthly",
        notification: dict[str, Any] | None = None,
        language: LanguageSchema | None = None,
        tags: list[str] | None = None,
        schedule_config: ScheduleConfigSchema | None = None,
        worker: Worker | None = None,
    ) -> Schedule:
        language = _language if language is None else language
        schedule_config = (
            _schedule_config if schedule_config is None else schedule_config
        )
        schedule = Schedule(
            name=name,
            tags=tags or ["nopic"],
            category=category,
            config=schedule_config.model_dump(
                mode="json", context={"show_secrets": True}
            ),
            enabled=True,
            language_code=language.code,
            language_name_native=language.name_native,
            language_name_en=language.name_en,
            periodicity=periodicity,
            notification=notification,
        )
        schedule_duration = ScheduleDuration(
            value=DEFAULT_SCHEDULE_DURATION.value,
            on=DEFAULT_SCHEDULE_DURATION.on,
            default=True,
        )
        schedule_duration.worker = worker
        schedule.durations.append(schedule_duration)
        dbsession.add(schedule)
        dbsession.flush()
        return schedule

    return _create_schedule


@pytest.fixture
def schedule(create_schedule: Callable[..., Schedule]):
    return create_schedule()


@pytest.fixture(scope="module")
def create_event():
    def _create_event(code: str, timestamp: datetime.datetime, **kwargs: Any):
        event = {"code": code, "timestamp": timestamp}
        event.update(kwargs)
        return event

    return _create_event


@pytest.fixture
def create_requested_task(
    dbsession: OrmSession,
    create_schedule: Callable[..., Schedule],
    worker: Worker,
    create_event: Callable[..., Any],
    schedule_config: ScheduleConfigSchema,
):
    _schedule_config = schedule_config
    _worker = worker

    def _create_requested_task(
        *,
        schedule_name: str = "testschedule",
        status: TaskStatus = TaskStatus.requested,
        requested_by: str = "testuser",
        priority: int = 0,
        worker: Worker | None = None,
        request_date: datetime.datetime | None = None,
        schedule_config: ScheduleConfigSchema | None = None,
    ):
        now = getnow()
        events = list(TaskStatus)

        timestamp = [(event.value, request_date or now) for event in events]
        events = [
            create_event(event.value, get_timestamp_for_status(timestamp, event.value))
            for event in events
        ]

        schedule_config = (
            _schedule_config if schedule_config is None else schedule_config
        )

        schedule = get_schedule_or_none(dbsession, schedule_name=schedule_name)
        if schedule is None:
            schedule = create_schedule(
                name=schedule_name, schedule_config=schedule_config
            )

        requested_task = RequestedTask(
            status=status,
            timestamp=timestamp,
            updated_at=request_date or now,
            events=events,
            requested_by=requested_by,
            priority=priority,
            config=expanded_config(schedule_config).model_dump(
                mode="json", context={"show_secrets": True}
            ),
            upload={},
            notification={},
            original_schedule_name=schedule_name,
        )
        requested_task.schedule = schedule
        requested_task.worker = _worker if worker is None else worker
        dbsession.add(requested_task)
        dbsession.flush()
        return requested_task

    return _create_requested_task


@pytest.fixture
def requested_task(
    create_requested_task: Callable[..., RequestedTask],
    schedule_config: ScheduleConfigSchema,
):
    return create_requested_task(schedule_config=schedule_config)


@pytest.fixture
def requested_tasks(
    create_requested_task: Callable[..., RequestedTask],
    request: FixtureRequest,
    data_gen: Faker,
) -> list[RequestedTask]:
    """Adds requested tasks to the database using the num_requested_tasks mark."""
    mark = cast(
        Mark,
        request.node.get_closest_marker(  # pyright: ignore[reportUnknownMemberType]
            "num_requested_tasks"
        ),
    )
    if mark and len(mark.args) > 0:
        num_requested_tasks = int(mark.args[0])
    else:
        num_requested_tasks = 10

    tasks: list[RequestedTask] = []
    for _ in range(num_requested_tasks):
        tasks.append(create_requested_task(status=data_gen.task_status()))
    return tasks


@pytest.fixture
def create_task(
    create_requested_task: Callable[..., RequestedTask],
    worker: Worker,
    dbsession: OrmSession,
) -> Callable[..., Task]:
    _worker = worker

    def _create_task(
        *,
        schedule_name: str = "testschedule",
        status: TaskStatus = TaskStatus.requested,
        worker: Worker | None = None,
        requested_task: RequestedTask | None = None,
    ) -> Task:
        if requested_task is None:
            requested_task = create_requested_task(
                schedule_name=schedule_name, status=status
            )
        task = Task(
            updated_at=requested_task.updated_at,
            events=requested_task.events,
            debug={},
            status=requested_task.status,
            timestamp=requested_task.timestamp,
            requested_by=requested_task.requested_by,
            canceled_by=None,
            container={},
            priority=requested_task.priority,
            config=requested_task.config,
            notification=requested_task.notification,
            files={},
            upload=requested_task.upload,
            original_schedule_name=requested_task.original_schedule_name,
        )
        task.id = requested_task.id
        task.schedule_id = requested_task.schedule_id
        task.worker_id = _worker.id if worker is None else worker.id
        dbsession.add(task)
        dbsession.flush()
        return task

    return _create_task


@pytest.fixture
def task(create_task: Callable[..., Task]) -> Task:
    return create_task()


# @pytest.fixture
# def set_default_publisher() -> Generator[Callable]:
#     def _set_default_publisher(publisher: str):
#         constants.DEFAULT_PUBLISHER = publisher
#
#     yield _set_default_publisher
#     constants.DEFAULT_PUBLISHER = None  # Reset to default after test
