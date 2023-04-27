from datetime import datetime
from ipaddress import IPv4Address
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, select, text
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSON, JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    Session,
    mapped_column,
    relationship,
    selectinload,
)
from sqlalchemy.sql.schema import MetaData


class Base(MappedAsDataclass, DeclarativeBase):
    # This map details the specific transformation of types between Python and
    # PostgreSQL. This is only needed for the case where a specific PostgreSQL
    # type has to be used or when we want to ensure a specific setting (like the
    # timezone below)
    type_annotation_map = {
        Dict[str, Any]: JSONB,  # transform Python Dict[str, Any] into PostgreSQL JSONB
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
    type_annotation_map = {
        Dict[str, Any]: MutableDict.as_mutable(JSONB),
        List[Dict[str, Any]]: ARRAY(item_type=MutableDict.as_mutable(JSONB)),
        datetime: DateTime(timezone=False),
        List[str]: ARRAY(item_type=String),
        IPv4Address: INET,
    }
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
    mongo_val: Mapped[
        Optional[Dict[str, Any]]
    ]  # temporary backup of full mongo document
    mongo_id: Mapped[Optional[str]] = mapped_column(
        unique=True
    )  # temporary backup of mongo document id
    username: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[Optional[str]]
    email: Mapped[Optional[str]]
    scope: Mapped[Optional[Dict[str, Any]]]

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
    def get_or_none(
        cls, session: Session, username: str, fetch_ssh_keys: bool = False
    ) -> Optional["User"]:
        """Search DB for a user by username, returns None if not found
        If `fetch_ssh_keys` argument is True, ssh_keys are also immediately
        retrieved.
        """
        stmt = select(User).where(User.username == username)
        if fetch_ssh_keys:
            stmt = stmt.options(selectinload(User.ssh_keys))
        return session.execute(stmt).scalar_one_or_none()

    @classmethod
    def get_id_or_none(cls, session: Session, username: str) -> Optional[UUID]:
        """Search DB for a user by username and return its ID. Returns None if not
        found.
        """
        stmt = select(User.id).where(User.username == username)
        return session.execute(stmt).scalar_one_or_none()


class Sshkey(Base):
    __tablename__ = "sshkey"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    mongo_val: Mapped[
        Optional[Dict[str, Any]]
    ]  # temporary backup of full mongo document
    # Nota: there is no temporary backup of mongo document id because there is
    # none since this data was embedded inside the User document in Mongo
    name: Mapped[Optional[str]]
    fingerprint: Mapped[Optional[str]] = mapped_column(index=True)
    type: Mapped[Optional[str]]
    key: Mapped[Optional[str]]
    added: Mapped[Optional[datetime]]
    last_used: Mapped[Optional[datetime]]
    pkcs8_key: Mapped[Optional[str]]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), init=False)

    user: Mapped["User"] = relationship(back_populates="ssh_keys", init=False)


class Refreshtoken(Base):
    __tablename__ = "refresh_token"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    mongo_val: Mapped[
        Optional[Dict[str, Any]]
    ]  # temporary backup of full mongo document
    mongo_id: Mapped[Optional[str]] = mapped_column(
        unique=True
    )  # temporary backup of mongo document id
    token: Mapped[UUID] = mapped_column(server_default=text("uuid_generate_v4()"))
    expire_time: Mapped[datetime]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), init=False)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens", init=False)

    __table_args__ = (Index(None, user_id, token, unique=True),)


class Worker(Base):
    __tablename__ = "worker"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    mongo_val: Mapped[
        Optional[Dict[str, Any]]
    ]  # temporary backup of full mongo document
    mongo_id: Mapped[Optional[str]] = mapped_column(
        unique=True
    )  # temporary backup of mongo document id
    name: Mapped[str] = mapped_column(unique=True, index=True)
    selfish: Mapped[bool]
    cpu: Mapped[int]
    memory: Mapped[int] = mapped_column(type_=BigInteger)
    disk: Mapped[int] = mapped_column(type_=BigInteger)
    offliners: Mapped[List[str]]
    platforms: Mapped[Dict[str, Any]]
    last_seen: Mapped[Optional[datetime]]
    last_ip: Mapped[Optional[IPv4Address]]

    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), init=False)

    user: Mapped["User"] = relationship(back_populates="workers", init=False)

    tasks: Mapped[List["Task"]] = relationship(
        back_populates="worker", cascade="all", init=False
    )

    requested_tasks: Mapped[List["RequestedTask"]] = relationship(
        back_populates="worker", cascade="all", init=False
    )

    @classmethod
    def get_or_none(cls, session: Session, name: str) -> Optional["Worker"]:
        """Search DB for a worker by name, returns None if not found"""
        stmt = select(Worker).where(Worker.name == name)
        return session.execute(stmt).scalar_one_or_none()

    @classmethod
    def get_id_or_none(cls, session: Session, name: str) -> Optional[UUID]:
        """Search DB for a worker by name and return its ID. Returns None if not
        found.
        """
        stmt = select(Worker.id).where(Worker.name == name)
        return session.execute(stmt).scalar_one_or_none()


class Task(Base):
    __tablename__ = "task"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    mongo_val: Mapped[
        Optional[Dict[str, Any]]
    ]  # temporary backup of full mongo document
    mongo_id: Mapped[Optional[str]] = mapped_column(
        unique=True
    )  # temporary backup of mongo document id
    updated_at: Mapped[datetime] = mapped_column(index=True)
    events: Mapped[List[Dict[str, Any]]]
    debug: Mapped[Optional[Dict[str, Any]]]
    status: Mapped[str] = mapped_column(index=True)
    timestamp: Mapped[Dict[str, Any]]
    requested_by: Mapped[Optional[str]]
    canceled_by: Mapped[Optional[str]]
    container: Mapped[Optional[Dict[str, Any]]]
    priority: Mapped[int]
    config: Mapped[Dict[str, Any]] = mapped_column(MutableDict.as_mutable(JSON))
    notification: Mapped[Optional[Dict[str, Any]]]
    files: Mapped[Optional[Dict[str, Any]]]
    upload: Mapped[Optional[Dict[str, Any]]]

    schedule_id: Mapped[UUID] = mapped_column(ForeignKey("schedule.id"), init=False)

    schedule: Mapped["Schedule"] = relationship(
        back_populates="tasks", init=False, foreign_keys=[schedule_id]
    )

    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker.id"), init=False)

    worker: Mapped["Worker"] = relationship(back_populates="tasks", init=False)

    @classmethod
    def get_or_none_by_id(cls, session: Session, id: UUID) -> Optional["Task"]:
        """Search DB for a task by UUID, returns None if not found"""
        stmt = select(Task).where(Task.id == id)
        return session.execute(stmt).scalar_one_or_none()


class Schedule(Base):
    __tablename__ = "schedule"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    mongo_val: Mapped[
        Optional[Dict[str, Any]]
    ]  # temporary backup of full mongo document
    mongo_id: Mapped[Optional[str]] = mapped_column(
        unique=True
    )  # temporary backup of mongo document id
    name: Mapped[str] = mapped_column(unique=True, index=True)
    category: Mapped[str] = mapped_column(index=True)
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
        cascade="all",
        init=False,
        foreign_keys=[Task.schedule_id],
    )

    requested_tasks: Mapped[List["RequestedTask"]] = relationship(
        back_populates="schedule", cascade="all", init=False
    )

    durations: Mapped[List["ScheduleDuration"]] = relationship(
        back_populates="schedule", cascade="all", init=False
    )

    @classmethod
    def get_or_none(cls, session: Session, name: str) -> Optional["Schedule"]:
        """Search DB for a schedule by name, returns None if not found"""
        stmt = select(Schedule).where(Schedule.name == name)
        return session.execute(stmt).scalar_one_or_none()

    @classmethod
    def get_id_or_none(cls, session: Session, name: str) -> Optional[UUID]:
        """Search DB for a schedule by name, and return its ID.
        Returns None if not found"""
        stmt = select(Schedule.id).where(Schedule.name == name)
        return session.execute(stmt).scalar_one_or_none()


class ScheduleDuration(Base):
    __tablename__ = "schedule_duration"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    mongo_val: Mapped[
        Optional[Dict[str, Any]]
    ]  # temporary backup of full mongo document
    default: Mapped[bool]
    value: Mapped[int]
    on: Mapped[datetime]

    schedule_id: Mapped[UUID] = mapped_column(ForeignKey("schedule.id"), init=False)

    schedule: Mapped["Schedule"] = relationship(init=False)

    worker_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("worker.id"), init=False
    )

    worker: Mapped[Optional["Worker"]] = relationship(init=False)

    task_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("task.id"), init=False)

    task: Mapped[Optional["Task"]] = relationship(init=False)


class RequestedTask(Base):
    __tablename__ = "requested_task"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    mongo_val: Mapped[
        Optional[Dict[str, Any]]
    ]  # temporary backup of full mongo document
    mongo_id: Mapped[Optional[str]] = mapped_column(
        unique=True
    )  # temporary backup of mongo document id
    status: Mapped[str]
    timestamp: Mapped[Dict[str, Any]]
    updated_at: Mapped[datetime] = mapped_column(index=True)
    events: Mapped[List[Dict[str, Any]]]
    requested_by: Mapped[str]
    priority: Mapped[int]
    config: Mapped[Dict[str, Any]] = mapped_column(MutableDict.as_mutable(JSON))
    upload: Mapped[Dict[str, Any]]
    notification: Mapped[Optional[Dict[str, Any]]]

    schedule_id: Mapped[UUID] = mapped_column(ForeignKey("schedule.id"), init=False)

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
    def get_or_none_by_id(cls, session: Session, id: UUID) -> Optional["RequestedTask"]:
        """Search DB for a requested task by UUID, returns None if not found"""
        stmt = select(RequestedTask).where(RequestedTask.id == id)
        return session.execute(stmt).scalar_one_or_none()
