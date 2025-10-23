from pydantic import EmailStr, computed_field, field_validator

from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import NotEmptyString


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
