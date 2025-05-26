import re
from typing import Any

from pydantic import (
    EmailStr,
    Field,
    HttpUrl,
    create_model,
    field_validator,
    model_validator,
)

from zimfarm_backend.common import constants
from zimfarm_backend.common.enums import (
    DockerImageName,
    Offliner,
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
        # strip the image prefix out so we don't have to care about it later-on
        # should ideally be dynamic but this is based on the offliner/task_name
        # which we don't have access to here. awaiting additional registry usage to fix
        return re.sub(r"^ghcr.io/", "", v)


class ScheduleConfigSchema(BaseModel):
    task_name: Offliner
    warehouse_path: WarehousePath
    image: DockerImageSchema
    resources: ResourcesSchema
    flags: dict[str, Any]
    platform: Platform | None = None
    artifacts_globs: list[NotEmptyString] = Field(default_factory=list)
    monitor: bool

    @staticmethod
    def get_offliner_schema(offliner: Offliner) -> type[BaseModel]:
        return {
            Offliner.mwoffliner: MWOfflinerFlagsSchema,
            Offliner.youtube: YoutubeFlagsSchema,
            Offliner.gutenberg: GutenbergFlagsSchema,
            Offliner.phet: PhetFlagsSchema,
            Offliner.sotoki: SotokiFlagsSchema,
            Offliner.nautilus: (
                NautilusFlagsSchemaRelaxed
                if constants.NAUTILUS_USE_RELAXED_SCHEMA
                else NautilusFlagsSchema
            ),
            Offliner.ted: TedFlagsSchema,
            Offliner.openedx: OpenedxFlagsSchema,
            Offliner.zimit: (
                ZimitFlagsSchemaRelaxed
                if constants.ZIMIT_USE_RELAXED_SCHEMA
                else ZimitFlagsSchema
            ),
            Offliner.kolibri: KolibriFlagsSchema,
            Offliner.wikihow: WikihowFlagsSchema,
            Offliner.ifixit: IFixitFlagsSchema,
            Offliner.freecodecamp: FreeCodeCampFlagsSchema,
            Offliner.devdocs: DevDocsFlagsSchema,
            Offliner.mindtouch: MindtouchFlagsSchema,
        }.get(offliner, BaseModel)

    @model_validator(mode="before")
    def validate_flags(cls, data: dict[str, Any]) -> dict[str, Any]:  # noqa: N805
        if "task_name" in data and "flag" in data:
            schema = cls.get_offliner_schema(data["task_name"])
            data["flags"] = schema.model_validate(data["flags"]).model_dump(mode="json")
        return data


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


PlatformsLimitSchema = (  # pyright: ignore[reportUnknownVariableType, reportCallIssue]
    create_model(
        "PlatformsLimitSchema",
        **{  # pyright: ignore[reportArgumentType]
            platform.name: (ZIMPlatformValue, ...) for platform in Platform.all()
        },
    )
)
