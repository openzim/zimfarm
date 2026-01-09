import datetime
import math
import pathlib
import re
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    HttpUrl,
    SerializeAsAny,
    field_validator,
)

from zimfarm_backend.common.enums import DockerImageName
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


class BaseScheduleConfigSchema(BaseModel):
    warehouse_path: WarehousePathField
    resources: ResourcesSchema
    offliner: SerializeAsAny[BaseModel]
    platform: PlatformField | None = None
    artifacts_globs: list[NotEmptyString] = Field(default_factory=list)
    monitor: bool


class ScheduleConfigSchema(BaseScheduleConfigSchema):
    image: DockerImageSchema


class ExpandedScheduleDockerImageSchema(BaseModel):
    name: str
    tag: str


class ExpandedScheduleConfigSchema(BaseScheduleConfigSchema):
    image: ExpandedScheduleDockerImageSchema
    mount_point: pathlib.Path
    command: list[NotEmptyString]
    str_command: str


class EventNotificationSchema(BaseModel):
    mailgun: list[EmailStr] | None = None
    webhook: list[HttpUrl] | None = None
    slack: list[SlackTarget] | None = None


class ScheduleNotificationSchema(BaseModel):
    requested: EventNotificationSchema | None = None
    started: EventNotificationSchema | None = None
    ended: EventNotificationSchema | None = None


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
