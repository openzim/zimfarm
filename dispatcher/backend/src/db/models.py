import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import JSONB
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
    type_annotation_map = {
        Dict[str, Any]: JSONB,  # transform Python Dict[str, Any] into PostgreSQL JSONB
        datetime: DateTime(
            timezone=False
        ),  # transform Python datetime into PostgreSQL Datetime without timezone
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
    id: Mapped[uuid.UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    mongo_val: Mapped[Optional[Dict[str, Any]]]
    mongo_id: Mapped[Optional[str]] = mapped_column(unique=True)
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


class Sshkey(Base):
    __tablename__ = "sshkey"
    id: Mapped[uuid.UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    mongo_val: Mapped[Optional[Dict[str, Any]]]
    name: Mapped[Optional[str]]
    fingerprint: Mapped[Optional[str]] = mapped_column(index=True)
    type: Mapped[Optional[str]]
    key: Mapped[Optional[str]]
    added: Mapped[Optional[datetime]]
    last_used: Mapped[Optional[datetime]]
    pkcs8_key: Mapped[Optional[str]]
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), init=False)

    user: Mapped["User"] = relationship(back_populates="ssh_keys", init=False)


class Refreshtoken(Base):
    __tablename__ = "refresh_token"
    id: Mapped[uuid.UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    mongo_val: Mapped[Optional[Dict[str, Any]]]
    mongo_id: Mapped[Optional[str]] = mapped_column(unique=True)
    token: Mapped[uuid.UUID] = mapped_column(server_default=text("uuid_generate_v4()"))
    expire_time: Mapped[datetime]
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), init=False)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens", init=False)

    __table_args__ = (Index(None, user_id, token, unique=True),)
