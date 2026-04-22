from datetime import datetime
from ipaddress import IPv4Address
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    false,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSON, JSONB
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)
from sqlalchemy.sql.schema import MetaData


class Base(MappedAsDataclass, DeclarativeBase):
    # This map details the specific transformation of types between Python and
    # PostgreSQL. This is only needed for the case where a specific PostgreSQL
    # type has to be used or when we want to ensure a specific setting (like the
    # timezone below)
    type_annotation_map = {  # noqa: RUF012
        dict[str, Any]: MutableDict.as_mutable(
            JSONB
        ),  # transform Python Dict[str, Any] into PostgreSQL JSONB
        list[dict[str, Any]]: MutableList.as_mutable(JSONB),
        list[tuple[str, Any]]: MutableList.as_mutable(JSONB),
        datetime: DateTime(
            timezone=False
        ),  # transform Python datetime into PostgreSQL Datetime without timezone
        list[str]: ARRAY(
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


class Account(Base):
    __tablename__ = "account"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    # Due to account registration coming from both Kiwix SSO and local registration,
    # there is a possibility of having usernames from the SSO conflicting with
    # a local account, thus, username field isn't distinct. While username will mostly
    # be set for locally registered accounts, display_name will set for all accounts
    username: Mapped[str | None] = mapped_column(unique=True, index=True)
    display_name: Mapped[str]
    password_hash: Mapped[str | None]
    scope: Mapped[dict[str, Any] | None]
    role: Mapped[str] = mapped_column(server_default="custom")
    deleted: Mapped[bool] = mapped_column(default=False, server_default=false())
    idp_sub: Mapped[UUID | None] = mapped_column(unique=True, index=True, default=None)

    refresh_tokens: Mapped[list["Refreshtoken"]] = relationship(
        back_populates="account", cascade="all, delete-orphan", init=False
    )

    workers: Mapped[list["Worker"]] = relationship(
        back_populates="account", cascade="all, delete-orphan", init=False
    )


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
    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker.id"), init=False)

    worker: Mapped["Worker"] = relationship(back_populates="ssh_keys", init=False)


class Refreshtoken(Base):
    __tablename__ = "refresh_token"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    token: Mapped[UUID] = mapped_column(server_default=text("uuid_generate_v4()"))
    expire_time: Mapped[datetime]
    account_id: Mapped[UUID] = mapped_column(ForeignKey("account.id"), init=False)

    account: Mapped["Account"] = relationship(
        back_populates="refresh_tokens", init=False
    )

    __table_args__ = (
        Index("ix_refresh_token_account_id_token", "account_id", "token", unique=True),
    )


class Worker(Base):
    __tablename__ = "worker"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(unique=True, index=True)
    selfish: Mapped[bool]
    total_cpu: Mapped[int]
    total_memory: Mapped[int] = mapped_column(type_=BigInteger)
    total_disk: Mapped[int] = mapped_column(type_=BigInteger)
    offliners: Mapped[list[str]]
    platforms: Mapped[dict[str, Any]]
    last_seen: Mapped[datetime | None]
    last_ip: Mapped[IPv4Address | None]
    available_cpu: Mapped[int]
    available_memory: Mapped[int] = mapped_column(type_=BigInteger)
    available_disk: Mapped[int] = mapped_column(type_=BigInteger)
    deleted: Mapped[bool] = mapped_column(default=False, server_default=false())
    contexts: Mapped[dict[str, Any]] = mapped_column(
        default_factory=dict, server_default="{}"
    )
    # worker voluntarily cordoned itself from requesting new tasks
    cordoned: Mapped[bool] = mapped_column(default=False, server_default=false())
    # admin disabled the worker from requesting new tasks
    admin_disabled: Mapped[bool] = mapped_column(default=False, server_default=false())
    docker_image_hash: Mapped[str | None] = mapped_column(default=None)
    docker_image_created_at: Mapped[datetime | None] = mapped_column(default=None)

    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("account.id"), init=False, unique=True
    )

    account: Mapped["Account"] = relationship(back_populates="workers", init=False)

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="worker", cascade="all", init=False
    )

    requested_tasks: Mapped[list["RequestedTask"]] = relationship(
        back_populates="worker", cascade="all", init=False
    )

    ssh_keys: Mapped[list["Sshkey"]] = relationship(
        back_populates="worker", cascade="all, delete-orphan", init=False
    )


class Task(Base):
    __tablename__ = "task"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    updated_at: Mapped[datetime] = mapped_column(index=True)
    events: Mapped[list[dict[str, Any]]]
    debug: Mapped[dict[str, Any]]
    status: Mapped[str] = mapped_column(index=True)
    requested_by_id: Mapped[UUID] = mapped_column(ForeignKey("account.id"), init=False)
    canceled_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("account.id"), init=False
    )
    container: Mapped[dict[str, Any]]
    priority: Mapped[int]
    # config must be JSON instead of JSONB so that we can query on dict item value
    config: Mapped[dict[str, Any]] = mapped_column(MutableDict.as_mutable(JSON))
    notification: Mapped[dict[str, Any]]
    upload: Mapped[dict[str, Any]]
    original_recipe_name: Mapped[str]
    context: Mapped[str] = mapped_column(default="", server_default="")
    timestamp: Mapped[list[tuple[str, Any]]] = mapped_column(default_factory=list)

    recipe_id: Mapped[UUID | None] = mapped_column(ForeignKey("recipe.id"), init=False)

    recipe: Mapped["Recipe | None"] = relationship(
        back_populates="tasks", init=False, foreign_keys=[recipe_id]
    )

    worker_id: Mapped[UUID] = mapped_column(ForeignKey("worker.id"), init=False)

    worker: Mapped["Worker"] = relationship(back_populates="tasks", init=False)

    # the exact offliner definition that was used to create the task
    offliner_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("offliner_definition.id"), init=False
    )
    offliner_definition: Mapped["OfflinerDefinition"] = relationship(init=False)

    files: Mapped[list["File"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        init=False,
        passive_deletes=True,
    )
    requested_by: Mapped["Account"] = relationship(
        init=False, foreign_keys=[requested_by_id]
    )
    canceled_by: Mapped["Account | None"] = relationship(
        init=False, foreign_keys=[canceled_by_id]
    )


class File(Base):
    __tablename__ = "file"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    name: Mapped[str]
    status: Mapped[str]
    size: Mapped[int | None] = mapped_column(default=None, type_=BigInteger)

    cms_on: Mapped[datetime | None] = mapped_column(default=None)
    cms_notified: Mapped[bool | None] = mapped_column(default=None, index=True)

    # Timestamp fields
    created_timestamp: Mapped[datetime | None] = mapped_column(default=None)
    uploaded_timestamp: Mapped[datetime | None] = mapped_column(default=None)
    failed_timestamp: Mapped[datetime | None] = mapped_column(default=None)
    # Check fields
    check_timestamp: Mapped[datetime | None] = mapped_column(default=None)
    check_result: Mapped[int | None] = mapped_column(default=None)
    # if filename exists, then check result was uploaded successfully
    check_filename: Mapped[str | None] = mapped_column(default=None)
    check_upload_timestamp: Mapped[datetime | None] = mapped_column(default=None)
    info: Mapped[dict[str, Any]] = mapped_column(
        default_factory=dict, server_default="{}"
    )

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("task.id", ondelete="CASCADE"), init=False
    )

    task: Mapped["Task"] = relationship(back_populates="files", init=False)

    __table_args__ = (UniqueConstraint("task_id", "name"),)


class Recipe(Base):
    __tablename__ = "recipe"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(unique=True, index=True)
    category: Mapped[str] = mapped_column(index=True)
    # config must be JSON instead of JSONB so that we can query on dict item value.
    config: Mapped[dict[str, Any]] = mapped_column(MutableDict.as_mutable(JSON))
    enabled: Mapped[bool]
    language_code: Mapped[str] = mapped_column(index=True)
    tags: Mapped[list[str]] = mapped_column(index=True)
    periodicity: Mapped[str]
    notification: Mapped[dict[str, Any] | None]
    is_valid: Mapped[bool] = mapped_column(default=True, server_default=true())
    # context that a worker must have to run this recipe
    context: Mapped[str] = mapped_column(default="", server_default="", index=True)
    archived: Mapped[bool] = mapped_column(default=False, server_default=false())
    similarity_data: Mapped[list[str]] = mapped_column(
        default_factory=list, server_default="{}", index=True
    )

    # use_alter is mandatory for alembic to break the dependency cycle
    # but it is still not totally handled automatically, the migration
    # has been partially modified to create the FK afterwards
    most_recent_task_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("task.id", use_alter=True), init=False
    )
    most_recent_task: Mapped[Optional["Task"]] = relationship(
        init=False, foreign_keys=[most_recent_task_id]
    )

    offliner_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("offliner_definition.id"), init=False
    )
    offliner_definition: Mapped["OfflinerDefinition"] = relationship(init=False)

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="recipe",
        cascade="save-update, merge, refresh-expire",
        init=False,
        foreign_keys=[Task.recipe_id],
    )

    requested_tasks: Mapped[list["RequestedTask"]] = relationship(
        back_populates="recipe",
        cascade="save-update, merge, refresh-expire",
        init=False,
    )

    durations: Mapped[list["RecipeDuration"]] = relationship(
        back_populates="recipe", cascade="all", init=False
    )

    history_entries: Mapped[list["RecipeHistory"]] = relationship(
        back_populates="recipe",
        cascade="all, delete",
        passive_deletes=True,
        init=False,
        default_factory=list,
        # return the history entries in descending order of created_at
        order_by="RecipeHistory.created_at.desc()",
    )

    blobs: Mapped[list["Blob"]] = relationship(
        back_populates="recipe",
        init=False,
        default_factory=list,
    )


class RecipeHistory(Base):
    __tablename__ = "recipe_history"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    recipe_id: Mapped[UUID] = mapped_column(
        ForeignKey("recipe.id", ondelete="CASCADE"), init=False
    )
    author_id: Mapped[UUID] = mapped_column(ForeignKey("account.id"), init=False)
    created_at: Mapped[datetime]
    comment: Mapped[str | None]
    name: Mapped[str]
    category: Mapped[str]
    config: Mapped[dict[str, Any]] = mapped_column(MutableDict.as_mutable(JSON))
    enabled: Mapped[bool]
    language_code: Mapped[str]
    tags: Mapped[list[str]]
    periodicity: Mapped[str]
    offliner_definition_version: Mapped[str | None]
    context: Mapped[str] = mapped_column(default="", server_default="")
    archived: Mapped[bool] = mapped_column(default=False, server_default=false())
    notification: Mapped[dict[str, Any] | None] = mapped_column(
        default_factory=dict, server_default="{}"
    )

    recipe: Mapped["Recipe"] = relationship(
        back_populates="history_entries", init=False
    )
    author: Mapped["Account"] = relationship(init=False)


class RecipeDuration(Base):
    __tablename__ = "recipe_duration"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    default: Mapped[bool]
    value: Mapped[int]
    on: Mapped[datetime]

    recipe_id: Mapped[UUID] = mapped_column(ForeignKey("recipe.id"), init=False)

    recipe: Mapped["Recipe"] = relationship(init=False)

    worker_id: Mapped[UUID | None] = mapped_column(ForeignKey("worker.id"), init=False)

    worker: Mapped[Optional["Worker"]] = relationship(init=False)

    __table_args__ = (UniqueConstraint("recipe_id", "worker_id"),)


class RequestedTask(Base):
    __tablename__ = "requested_task"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    status: Mapped[str]
    updated_at: Mapped[datetime] = mapped_column(index=True)
    events: Mapped[list[dict[str, Any]]]
    requested_by_id: Mapped[UUID] = mapped_column(ForeignKey("account.id"), init=False)
    priority: Mapped[int]
    # config must be JSON instead of JSONB so that we can query on dict item value
    config: Mapped[dict[str, Any]] = mapped_column(MutableDict.as_mutable(JSON))
    upload: Mapped[dict[str, Any]]
    notification: Mapped[dict[str, Any]]
    original_recipe_name: Mapped[str]
    # context requirement from the recipe when the recipe was created
    context: Mapped[str] = mapped_column(default="", server_default="")

    timestamp: Mapped[list[tuple[str, Any]]] = mapped_column(default_factory=list)

    recipe_id: Mapped[UUID | None] = mapped_column(ForeignKey("recipe.id"), init=False)

    recipe: Mapped["Recipe | None"] = relationship(
        back_populates="requested_tasks", init=False
    )

    worker_id: Mapped[UUID | None] = mapped_column(ForeignKey("worker.id"), init=False)

    worker: Mapped["Worker | None"] = relationship(
        back_populates="requested_tasks", init=False
    )
    # the exact offliner definition that was used to create the requested task
    offliner_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("offliner_definition.id"), init=False
    )
    offliner_definition: Mapped["OfflinerDefinition"] = relationship(init=False)
    requested_by: Mapped["Account"] = relationship(init=False)

    __table_args__ = (UniqueConstraint("recipe_id"),)


class OfflinerDefinition(Base):
    __tablename__ = "offliner_definition"
    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    offliner: Mapped[str]
    schema: Mapped[dict[str, Any]] = mapped_column(MutableDict.as_mutable(JSON))
    version: Mapped[str]
    created_at: Mapped[datetime]

    __table_args__ = (UniqueConstraint("offliner", "version"),)


class Offliner(Base):
    __tablename__ = "offliner"
    id: Mapped[str] = mapped_column(primary_key=True)
    base_model: Mapped[str]
    docker_image_name: Mapped[str]
    command_name: Mapped[str]
    ci_secret_hash: Mapped[str | None]


class Blob(Base):
    __tablename__ = "blob"

    id: Mapped[UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    recipe_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("recipe.id", ondelete="SET NULL"), init=False
    )
    flag_name: Mapped[str]
    kind: Mapped[str]
    url: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=text("CURRENT_TIMESTAMP")
    )
    checksum: Mapped[str]  # SHA-256 checksum of blob

    comments: Mapped[str | None] = mapped_column(default=None)
    content: Mapped[bytes | None] = mapped_column(default=None)

    recipe: Mapped["Recipe | None"] = relationship(init=False, back_populates="blobs")

    __table_args__ = (UniqueConstraint("recipe_id", "flag_name", "checksum"),)
