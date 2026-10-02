from typing import Self

from pydantic import Field, model_validator

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    LimitFieldMax200,
    NotEmptyString,
    SkipField,
)
from zimfarm_backend.common.schemas.models import BaseAccountCreateUpdateSchema


class PasswordUpdateSchema(BaseModel):
    """
    Schema for updating an account's password
    """

    # accounts with elevated permissions can omit the current password
    current: NotEmptyString | None = None
    new: NotEmptyString | None


class AccountCreateSchema(BaseAccountCreateUpdateSchema):
    """
    Schema for creating an account
    """

    password: NotEmptyString | None = Field(default=None, min_length=8)

    @model_validator(mode="after")
    def check_username_and_password(self) -> Self:
        if self.password and not self.username:
            raise ValueError("Username must be set when password is set.")
        return self

    @model_validator(mode="after")
    def check_username_and_displayname(self) -> Self:
        if not (self.username or self.display_name):
            raise ValueError("Display name or username must be set.")

        if not self.display_name:
            self.display_name = self.username

        return self


class AccountsGetSchema(BaseModel):
    skip: SkipField = 0
    limit: LimitFieldMax200 = 20
    username: NotEmptyString | None = None
    show_workers: bool = True  # show accounts which have "worker" role
    show_viewers: bool = True  # show accounts which have "viewer" role
