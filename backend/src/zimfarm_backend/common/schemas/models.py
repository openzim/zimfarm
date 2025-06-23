import pathlib
import re
from typing import Union

from pydantic import (
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
)

from zimfarm_backend.common import constants
from zimfarm_backend.common.enums import (
    DockerImageName,
    Platform,
    WarehousePath,
)
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    ZIMCPU,
    NotEmptyString,
    SlackTarget,
    ZIMDisk,
    ZIMLangCode,
    ZIMMemory,
    ZIMPlatformValue,
)
from zimfarm_backend.common.schemas.offliners import (
    DevDocsFlagsSchema,
    FreeCodeCampFlagsSchema,
    GutenbergFlagsSchema,
    IFixitFlagsSchema,
    KolibriFlagsSchema,
    MindtouchFlagsSchema,
    MWOfflinerFlagsSchema,
    NautilusFlagsSchema,
    NautilusFlagsSchemaRelaxed,
    OpenedxFlagsSchema,
    PhetFlagsSchema,
    SotokiFlagsSchema,
    TedFlagsSchema,
    WikihowFlagsSchema,
    YoutubeFlagsSchema,
    ZimitFlagsSchema,
    ZimitFlagsSchemaRelaxed,
)


class LanguageSchema(BaseModel):
    code: ZIMLangCode
    name_en: NotEmptyString
    name_native: NotEmptyString


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


OfflinerSchema = Union[  # noqa: UP007
    MWOfflinerFlagsSchema,
    YoutubeFlagsSchema,
    GutenbergFlagsSchema,
    PhetFlagsSchema,
    SotokiFlagsSchema,
    KolibriFlagsSchema,
    WikihowFlagsSchema,
    IFixitFlagsSchema,
    FreeCodeCampFlagsSchema,
    DevDocsFlagsSchema,
    MindtouchFlagsSchema,
    OpenedxFlagsSchema,
    TedFlagsSchema,
    ZimitFlagsSchemaRelaxed if constants.ZIMIT_USE_RELAXED_SCHEMA else ZimitFlagsSchema,
    (
        NautilusFlagsSchemaRelaxed
        if constants.NAUTILUS_USE_RELAXED_SCHEMA
        else NautilusFlagsSchema
    ),
]


class BaseScheduleConfigSchema(BaseModel):
    warehouse_path: WarehousePath
    resources: ResourcesSchema
    offliner: OfflinerSchema = Field(discriminator="offliner_id")
    platform: Platform | None = None
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


class PlaftormLimitSchema(BaseModel):
    platform: Platform
    limit: ZIMPlatformValue


class PlatformsLimitSchema(BaseModel):
    limits: list[PlaftormLimitSchema]


class Paginator(BaseModel):
    nb_records: int = Field(serialization_alias="count")
    skip: int
    limit: int
    page_size: int


def calculate_pagination_metadata(
    *,
    nb_records: int,
    skip: int,
    limit: int,
    page_size: int,
) -> Paginator:
    if nb_records == 0:
        return Paginator(
            nb_records=0,
            skip=skip,
            limit=limit,
            page_size=0,
        )
    return Paginator(
        nb_records=nb_records,
        skip=skip,
        limit=limit,
        page_size=min(page_size, nb_records),
    )
