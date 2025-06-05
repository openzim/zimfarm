import re

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
    ScheduleCategory,
    SchedulePeriodicity,
    WarehousePath,
)
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    ZIMCPU,
    NotEmptyString,
    ScheduleNameField,
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


OfflinerSchema = (
    MWOfflinerFlagsSchema
    | YoutubeFlagsSchema
    | GutenbergFlagsSchema
    | PhetFlagsSchema
    | SotokiFlagsSchema
    | NautilusFlagsSchemaRelaxed
    if constants.NAUTILUS_USE_RELAXED_SCHEMA
    else (
        NautilusFlagsSchema
        | TedFlagsSchema
        | OpenedxFlagsSchema
        | ZimitFlagsSchemaRelaxed
        if constants.ZIMIT_USE_RELAXED_SCHEMA
        else ZimitFlagsSchema
        | KolibriFlagsSchema
        | WikihowFlagsSchema
        | IFixitFlagsSchema
        | FreeCodeCampFlagsSchema
        | DevDocsFlagsSchema
        | MindtouchFlagsSchema
    )
)


class ScheduleConfigSchema(BaseModel):
    warehouse_path: WarehousePath
    image: DockerImageSchema
    resources: ResourcesSchema
    flags: OfflinerSchema = Field(  # pyright: ignore[reportInvalidTypeForm]
        discriminator="offliner_id"
    )
    platform: Platform | None = None
    artifacts_globs: list[NotEmptyString] = Field(default_factory=list)
    monitor: bool


class EventNotificationSchema(BaseModel):
    mailgun: list[EmailStr] | None = None
    webhook: list[HttpUrl] | None = None
    slack: list[SlackTarget] | None = None


class ScheduleNotificationSchema(BaseModel):
    requested: EventNotificationSchema | None = None
    started: EventNotificationSchema | None = None
    ended: EventNotificationSchema | None = None


class ScheduleSchema(BaseModel):
    name: ScheduleNameField
    language: LanguageSchema
    category: ScheduleCategory
    periodicity: SchedulePeriodicity
    tags: list[NotEmptyString] = Field(default_factory=list)
    enabled: bool
    config: ScheduleConfigSchema
    notification: ScheduleNotificationSchema | None = None


class PlaftormLimitSchema(BaseModel):
    platform: Platform
    limit: ZIMPlatformValue


class PlatformsLimitSchema(BaseModel):
    limits: list[PlaftormLimitSchema]
