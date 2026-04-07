from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    LimitFieldMax200,
    NotEmptyString,
    SkipField,
)


class PasswordUpdateSchema(BaseModel):
    """
    Schema for updating an account's password
    """

    # accounts with elevated permissions can omit the current password
    current: NotEmptyString | None = None
    new: NotEmptyString | None


class AccountCreateSchema(BaseModel):
    """
    Schema for creating an account
    """

    username: NotEmptyString
    password: NotEmptyString
    role: RoleEnum


class AccountsGetSchema(BaseModel):
    skip: SkipField = 0
    limit: LimitFieldMax200 = 20
    username: NotEmptyString | None = None
    show_workers: bool = False  # show accounts which have "worker" role
    show_viewers: bool = False  # show accounts which have "viewer" role
