import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)


class Base(MappedAsDataclass, DeclarativeBase):
    type_annotation_map = {Dict[str, Any]: JSONB, datetime: DateTime(timezone=True)}
    pass


class User(Base):
    __tablename__ = "user"
    id: Mapped[uuid.UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    mongo_val: Mapped[Optional[Dict[str, Any]]]
    mongo_id: Mapped[Optional[str]] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[Optional[str]]
    email: Mapped[Optional[str]]
    scope: Mapped[Optional[Dict[str, Any]]]

    ssh_keys: Mapped[List["Sshkey"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", init=False
    )


class Sshkey(Base):
    __tablename__ = "sshkey"
    id: Mapped[uuid.UUID] = mapped_column(
        init=False, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    mongo_val: Mapped[Optional[Dict[str, Any]]]
    name: Mapped[Optional[str]]
    fingerprint: Mapped[Optional[str]]
    type: Mapped[Optional[str]]
    key: Mapped[Optional[str]]
    added: Mapped[Optional[datetime]]
    last_used: Mapped[Optional[datetime]]
    pkcs8_key: Mapped[Optional[str]]
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), init=False)

    user: Mapped["User"] = relationship(back_populates="ssh_keys", init=False)
