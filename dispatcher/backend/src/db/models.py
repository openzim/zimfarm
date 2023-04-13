from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, select, text
from sqlalchemy.dialects.postgresql import JSONB
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
