import datetime
import math
import pathlib
import re
from typing import Any, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    HttpUrl,
    SerializeAsAny,
    computed_field,
    field_validator,
    model_validator,
)

from zimfarm_backend.common.enums import DockerImageName
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.common.schemas import BaseModel as ZimfarmBaseModel
from zimfarm_backend.common.schemas.fields import (
    ZIMCPU,
    NotEmptyString,
    PlatformField,
    SlackTarget,
    WarehousePathField,
    ZIMDisk,
    ZIMLangCode,
    ZIMMemory,
)


class LanguageSchema(BaseModel):
    code: ZIMLangCode
    name: NotEmptyString


class ResourcesSchema(BaseModel):
    cpu: ZIMCPU
    memory: ZIMMemory
    disk: ZIMDisk
    shm: ZIMMemory | None = None
    cap_add: list[NotEmptyString] = Field(default_factory=list)
    cap_drop: list[NotEmptyString] = Field(default_factory=list)


class DockerImageSchema(BaseModel):
    name: DockerImageName
    tag: NotEmptyString

    @field_validator("name", mode="before")
    def validate_name(cls, v: str) -> str:  # noqa: N805
        # docker images can have a prefix, e.g. ghcr.io/
        # set mode="before" and strip the image prefix so that the remaining name is
        # validated against the DockerImageName enum.
        return re.sub(r"^ghcr.io/", "", v)


class BaseRecipeConfigSchema(BaseModel):
    warehouse_path: WarehousePathField
    resources: ResourcesSchema
    offliner: SerializeAsAny[BaseModel]
    platform: PlatformField | None = None
    artifacts_globs: list[NotEmptyString] = Field(default_factory=list)
    monitor: bool


class RecipeConfigSchema(BaseRecipeConfigSchema):
    image: DockerImageSchema


class ExpandedRecipeDockerImageSchema(BaseModel):
    name: str
    tag: str


class ExpandedRecipeConfigSchema(BaseRecipeConfigSchema):
    image: ExpandedRecipeDockerImageSchema
    mount_point: pathlib.Path
    command: list[NotEmptyString]
    str_command: str


class EventNotificationSchema(BaseModel):
    mailgun: list[EmailStr] | None = Field(default_factory=list)
    webhook: list[HttpUrl] | None = Field(  # pyright: ignore[reportUnknownVariableType]
        default_factory=list
    )
    slack: list[SlackTarget] | None = Field(default_factory=list)


class RecipeNotificationSchema(BaseModel):
    requested: EventNotificationSchema | None = Field(
        default_factory=EventNotificationSchema
    )
    started: EventNotificationSchema | None = Field(
        default_factory=EventNotificationSchema
    )
    ended: EventNotificationSchema | None = Field(
        default_factory=EventNotificationSchema
    )


class Paginator(BaseModel):
    nb_records: int = Field(serialization_alias="count")
    skip: int
    limit: int
    page_size: int
    page: int


def calculate_pagination_metadata(
    *,
    nb_records: int,
    skip: int,
    limit: int,
    page_size: int,
) -> Paginator:
    page = math.floor(skip / limit) + 1 if limit > 0 else 1
    if nb_records == 0:
        return Paginator(
            nb_records=0,
            skip=skip,
            limit=limit,
            page_size=0,
            page=page,
        )
    return Paginator(
        nb_records=nb_records,
        skip=skip,
        limit=limit,
        page_size=min(page_size, nb_records),
        page=page,
    )


class FileCreateUpdateSchema(BaseModel):
    name: str
    task_id: UUID
    status: str
    size: int | None = None
    cms_on: datetime.datetime | None = None
    cms_notified: bool | None = None
    created_timestamp: datetime.datetime | None = None
    uploaded_timestamp: datetime.datetime | None = None
    failed_timestamp: datetime.datetime | None = None
    check_timestamp: datetime.datetime | None = None
    check_result: int | None = None
    check_filename: str | None = None
    check_upload_timestamp: datetime.datetime | None = None
    info: dict[str, Any] = Field(default_factory=dict)


class BaseAccountCreateUpdateSchema(BaseModel):
    username: NotEmptyString | None = Field(default=None, min_length=3)
    display_name: NotEmptyString | None = Field(default=None, min_length=3)
    idp_sub: UUID | None = None
    teams: list[NotEmptyString] | None = None
    role: RoleEnum

    @model_validator(mode="after")
    def check_role(self) -> Self:
        if self.role == RoleEnum.WORKER:
            raise ValueError("Worker accounts cannot be created.")
        return self

    @model_validator(mode="after")
    def restrict_teams_inclusion(self) -> Self:
        if (
            self.role
            in (
                RoleEnum.TEAM_EDITOR,
                RoleEnum.TEAM_EDITOR_REQUESTER,
                RoleEnum.TEAM_VIEWER,
            )
            and self.teams is None
        ):
            raise ValueError(
                f"Teams must be specified when setting role to {self.role}"
            )

        if (
            self.role
            not in (
                RoleEnum.TEAM_EDITOR,
                RoleEnum.TEAM_EDITOR_REQUESTER,
                RoleEnum.TEAM_VIEWER,
            )
            and self.teams
        ):
            raise ValueError(f"Teams must not be specified when role is {self.role}")

        return self


class AccountUpdateSchema(BaseAccountCreateUpdateSchema):
    """
    Schema for updating an account
    """

    role: RoleEnum | None = None  # pyright: ignore[reportIncompatibleVariableOverride]
    scope: dict[str, dict[str, bool]] | None = None

    @model_validator(mode="after")
    def check_exclusive_fields(self) -> Self:
        if self.role is not None and self.scope is not None:
            raise ValueError("Only one of role/scope must be set")
        return self


class DockerImageVersionSchema(ZimfarmBaseModel):
    """
    Schema for worker manager version information from GitHub Container Registry.
    """

    hash: str
    created_at: datetime.datetime


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


class TeamCreateSchema(BaseModel):
    name: NotEmptyString = Field(min_length=3)
    is_private: bool


class TeamUpdateSchema(BaseModel):
    name: NotEmptyString | None = Field(min_length=3, default=None)
    is_private: bool | None = None
    comment: NotEmptyString | None = None
