from datetime import datetime
from ipaddress import IPv4Address
from typing import Any, Dict, List, Optional, Type
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    false,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSON, JSONB
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    Session,
    declared_attr,
    mapped_column,
    relationship,
    selectinload,
)
from sqlalchemy.sql.schema import MetaData

from utils.check import raise_if, raise_if_none


class Base(MappedAsDataclass, DeclarativeBase):
    # This map details the specific transformation of types between Python and
    # PostgreSQL. This is only needed for the case where a specific PostgreSQL
    # type has to be used or when we want to ensure a specific setting (like the
    # timezone below)
    type_annotation_map = {
        Dict[str, Any]: MutableDict.as_mutable(
            JSONB
        ),  # transform Python Dict[str, Any] into PostgreSQL JSONB
        List[Dict[str, Any]]: MutableList.as_mutable(JSONB),
        datetime: DateTime(
            timezone=False
        ),  # transform Python datetime into PostgreSQL Datetime without timezone
        List[str]: ARRAY(
            item_type=String
        ),  # transform Python List[str] into PostgreSQL Array of strings
        IPv4Address: INET,  # transform Python IPV4Address into PostgreSQL INET
    }

    # This metadata specifies some naming conventions that will be used by
    # alembic to generate constraints names (indexes, unique constraints, ...)
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )
    pass


class User(Base):
    __tablename__ = "user"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    username: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[Optional[str]]
    email: Mapped[Optional[str]]
    scope: Mapped[Optional[Dict[str, Any]]]
    deleted: Mapped[bool] = mapped_column(default=False, server_default=false())

    ssh_keys: Mapped[List["Sshkey"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", init=False
    )

    refresh_tokens: Mapped[List["Refreshtoken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", init=False
    )

    workers: Mapped[List["Worker"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", init=False
    )

    @classmethod
    def check(
        cls,
        user: "User",
        exception_class: Type[Exception] = Exception,
        *exception_args: object,
    ) -> None:
        """Raise the exception passed in parameters if user is None or deleted."""
        raise_if_none(user, exception_class, *exception_args)
        raise_if(user.deleted, exception_class, *exception_args)

    @classmethod
    def get(
        cls,
        session: Session,
        username: str,
        exception_class: Type[Exception] = Exception,
        *exception_args: object,
        fetch_ssh_keys: bool = False,
        run_checks: bool = True,
    ) -> Optional["User"]:
        """Search DB for a user by username

        If the check of the user is not ok, raises the exception passed in
        parameters.
        SSH keys may be fetched from DB in the same call with `fetch_ssh_keys`
        """
        stmt = select(User).where(User.username == username)
        if fetch_ssh_keys:
            stmt = stmt.options(selectinload(User.ssh_keys))
        user = session.execute(stmt).scalar_one_or_none()
        if run_checks:
            cls.check(user, exception_class, *exception_args)
        return user


class Sshkey(Base):
    __tablename__ = "sshkey"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    name: Mapped[str]
    fingerprint: Mapped[str] = mapped_column(index=True)
    type: Mapped[str]
    key: Mapped[str]
    added: Mapped[datetime]
    pkcs8_key: Mapped[str]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), init=False)

    user: Mapped["User"] = relationship(back_populates="ssh_keys", init=False)


class Refreshtoken(Base):
    __tablename__ = "refresh_token"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    token: Mapped[UUID] = mapped_column(server_default=text("uuid_generate_v4()"))
    expire_time: Mapped[datetime]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), init=False)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens", init=False)

    @declared_attr
    def __table_args__(cls):
        return (Index(None, cls.user_id, cls.token, unique=True),)


class Worker(Base):
    __tablename__ = "worker"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(unique=True, index=True)
    selfish: Mapped[bool]
    cpu: Mapped[int]
    memory: Mapped[int] = mapped_column(type_=BigInteger)
    disk: Mapped[int] = mapped_column(type_=BigInteger)
    offliners: Mapped[List[str]]
    platforms: Mapped[Dict[str, Any]]
    last_seen: Mapped[Optional[datetime]]
    last_ip: Mapped[Optional[IPv4Address]]
    deleted: Mapped[bool] = mapped_column(default=False, server_default=false())

    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), init=False)

    user: Mapped["User"] = relationship(back_populates="workers", init=False)

    tasks: Mapped[List["Task"]] = relationship(
        back_populates="worker", cascade="all", init=False
    )

    requested_tasks: Mapped[List["RequestedTask"]] = relationship(
        back_populates="worker", cascade="all", init=False
    )

    @classmethod
    def get(
        cls,
        session: Session,
        name: str,
        exception_class: Type[Exception] = Exception,
        *exception_args: object,
        run_checks: bool = True,
    ) -> Optional["RequestedTask"]:
        """Search DB for a worker by name

        If the check of the worker are ok, raise thes exception passed
        in parameters
        """
        stmt = select(Worker).where(Worker.name == name)
        task = session.execute(stmt).scalar_one_or_none()
        if run_checks:
            raise_if_none(task, exception_class, *exception_args)
            raise_if(task.deleted, exception_class, *exception_args)
        return task


class Task(Base):
    __tablename__ = "task"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    updated_at: Mapped[datetime] = mapped_column(index=True)
    events: Mapped[List[Dict[str, Any]]]
    debug: Mapped[Dict[str, Any]]
    status: Mapped[str] = mapped_column(index=True)
    timestamp: Mapped[Dict[str, Any]]
    requested_by: Mapped[str]
    canceled_by: Mapped[Optional[str]]
    container: Mapped[Dict[str, Any]]
    priority: Mapped[int]
    # config must be JSON instead of JSONB so that we can query on dict item value
    config: Mapped[Dict[str, Any]] = mapped_column(MutableDict.as_mutable(JSON))
    notification: Mapped[Dict[str, Any]]
    files: Mapped[Dict[str, Any]]
    upload: Mapped[Dict[str, Any]]
    original_schedule_name: Mapped[str]

    schedule_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("schedule.id"), init=False
    )

    schedule: Mapped["Schedule"] = relationship(
        back_populates="tasks", init=False, foreign_keys=[schedule_id]
    )

    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker.id"), init=False)

    worker: Mapped["Worker"] = relationship(back_populates="tasks", init=False)

    @classmethod
    def get(
        cls,
        session: Session,
        id: UUID,
        exception_class: Type[Exception] = Exception,
        *exception_args: object,
    ) -> "Task":
        """Search DB for a task by UUID

        If the check of the task is not ok, raise thes exception passed in parameters"""
        stmt = select(Task).where(Task.id == id)
        task = session.execute(stmt).scalar_one_or_none()
        raise_if_none(task, exception_class, *exception_args)
        return task


class Schedule(Base):
    __tablename__ = "schedule"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(unique=True, index=True)
    category: Mapped[str] = mapped_column(index=True)
    # config must be JSON instead of JSONB so that we can query on dict item value
    config: Mapped[Dict[str, Any]] = mapped_column(MutableDict.as_mutable(JSON))
    enabled: Mapped[bool]
    language_code: Mapped[str] = mapped_column(index=True)
    language_name_native: Mapped[str]
    language_name_en: Mapped[str]
    tags: Mapped[List[str]] = mapped_column(index=True)
    periodicity: Mapped[str]
    notification: Mapped[Optional[Dict[str, Any]]]

    # use_alter is mandatory for alembic to break the dependency cycle
    # but it is still not totally handled automatically, the migration
    # has been partially modified to create the FK afterwards
    most_recent_task_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("task.id", use_alter=True), init=False
    )
    most_recent_task: Mapped[Optional["Task"]] = relationship(
        init=False, foreign_keys=[most_recent_task_id]
    )

    tasks: Mapped[List["Task"]] = relationship(
        back_populates="schedule",
        cascade="save-update, merge, refresh-expire",
        init=False,
        foreign_keys=[Task.schedule_id],
    )

    requested_tasks: Mapped[List["RequestedTask"]] = relationship(
        back_populates="schedule",
        cascade="save-update, merge, refresh-expire",
        init=False,
    )

    durations: Mapped[List["ScheduleDuration"]] = relationship(
        back_populates="schedule", cascade="all", init=False
    )

    @classmethod
    def get(
        cls,
        session: Session,
        name: str,
        exception_class: Type[Exception] = Exception,
        *exception_args: object,
        run_checks: bool = True,
    ) -> Optional["Schedule"]:
        """Search DB for a schedule by name

        If the check of the schedule is not ok, raise thes exception passed in
        parameters"""
        stmt = select(Schedule).where(Schedule.name == name)
        schedule = session.execute(stmt).scalar_one_or_none()
        if run_checks:
            raise_if_none(schedule, exception_class, *exception_args)
        return schedule


class ScheduleDuration(Base):
    __tablename__ = "schedule_duration"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    default: Mapped[bool]
    value: Mapped[int]
    on: Mapped[datetime]

    schedule_id: Mapped[UUID] = mapped_column(ForeignKey("schedule.id"), init=False)

    schedule: Mapped["Schedule"] = relationship(init=False)

    worker_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("worker.id"), init=False
    )

    worker: Mapped[Optional["Worker"]] = relationship(init=False)

    @declared_attr
    def __table_args__(cls):
        return (UniqueConstraint(cls.schedule_id, cls.worker_id),)


class RequestedTask(Base):
    __tablename__ = "requested_task"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    status: Mapped[str]
    timestamp: Mapped[Dict[str, Any]]
    updated_at: Mapped[datetime] = mapped_column(index=True)
    events: Mapped[List[Dict[str, Any]]]
    requested_by: Mapped[str]
    priority: Mapped[int]
    # config must be JSON instead of JSONB so that we can query on dict item value
    config: Mapped[Dict[str, Any]] = mapped_column(MutableDict.as_mutable(JSON))
    upload: Mapped[Dict[str, Any]]
    notification: Mapped[Dict[str, Any]]
    original_schedule_name: Mapped[str]

    schedule_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("schedule.id"), init=False
    )

    schedule: Mapped["Schedule"] = relationship(
        back_populates="requested_tasks", init=False
    )

    worker_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("worker.id"), init=False
    )

    worker: Mapped[Optional["Worker"]] = relationship(
        back_populates="requested_tasks", init=False
    )

    @classmethod
    def get(
        cls,
        session: Session,
        id: UUID,
        exception_class: Type[Exception] = Exception,
        *exception_args: object,
    ) -> "RequestedTask":
        """Search DB for a requested task by UUID

        If the check of the requested task is not ok, raise thes exception passed
        in parameters
        """
        stmt = select(RequestedTask).where(RequestedTask.id == id)
        task = session.execute(stmt).scalar_one_or_none()
        raise_if_none(task, exception_class, *exception_args)
        return task
