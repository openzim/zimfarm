import datetime
from typing import Any

from pydantic import EmailStr, Field, computed_field, field_validator

from zimfarm_backend.common import getnow
from zimfarm_backend.common.constants import SSH_KEY_EXPIRY_DURATION
from zimfarm_backend.common.roles import RoleEnum, get_role_for
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import NotEmptyString


class BaseUserSchema(BaseModel):
    """
    Base schema for reading a user model
    """

    username: str


class UserSchema(BaseUserSchema):
    """
    Schema for reading a user model
    """

    email: str | None
    scope: dict[str, Any] | None = Field(default=None)

    @computed_field
    @property
    def role(self) -> str:
        if self.scope is None:
            return "custom"
        return get_role_for(self.scope)


class BaseSshKeySchema(BaseModel):
    """
    Base schema for reading a ssh key model
    """

    key: str
    name: str
    type: str


class SshKeyRead(BaseSshKeySchema):
    """
    Schema for reading a ssh key model
    """

    added: datetime.datetime
    fingerprint: str
    pkcs8_key: str

    @computed_field
    @property
    def has_expired(self) -> bool:
        """Check if the key has expired (not active)"""
        return getnow() > self.added + datetime.timedelta(
            seconds=SSH_KEY_EXPIRY_DURATION
        )


class BaseUserWithSshKeysSchema(BaseUserSchema, BaseSshKeySchema):
    """
    Base schema for reading a user model with its ssh keys
    """


class SshKeyList(BaseModel):
    """
    Schema for reading a list of ssh keys
    """

    ssh_keys: list[SshKeyRead]


class UserSchemaWithSshKeys(UserSchema):
    """
    Schema for reading a user model with its ssh keys
    """

    ssh_keys: list[SshKeyRead]


class KeySchema(BaseModel):
    """
    Schema for creating a ssh key
    """

    key: NotEmptyString

    @field_validator("key", mode="after")
    @classmethod
    def validate_key(cls, value: str) -> str:
        value = value.strip()
        if len(value.split(" ")) != 3:  # noqa: PLR2004
            raise ValueError("Key does not appear to be an SSH public file.")
        return value

    @computed_field
    @property
    def name(self) -> str:
        return self.key.split(" ")[2]


class PasswordUpdateSchema(BaseModel):
    """
    Schema for updating a user's password
    """

    # users with elevated permissions can omit the current password
    current: NotEmptyString | None = None
    new: NotEmptyString


class UserCreateSchema(BaseModel):
    """
    Schema for creating a user
    """

    username: NotEmptyString
    password: NotEmptyString
    email: EmailStr
    role: RoleEnum


class UserUpdateSchema(BaseModel):
    """
    Schema for updating a user
    """

    email: EmailStr | None = None
    role: RoleEnum | None = None
