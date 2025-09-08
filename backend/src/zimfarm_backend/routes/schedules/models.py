from typing import Any
from uuid import UUID

from pydantic import Field

from zimfarm_backend.common.enums import (
    Offliner,
    ScheduleCategory,
    SchedulePeriodicity,
)
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    LimitFieldMax200,
    NotEmptyString,
    PlatformField,
    ScheduleNameField,
    SkipField,
    WarehousePathField,
    ZIMLangCode,
)
from zimfarm_backend.common.schemas.models import (
    DockerImageSchema,
    ResourcesSchema,
    ScheduleNotificationSchema,
)


class SchedulesGetSchema(BaseModel):
    skip: SkipField | None = None
    limit: LimitFieldMax200 | None = None
    category: list[ScheduleCategory] | None = None
    tag: list[NotEmptyString] | None = None
    lang: list[NotEmptyString] | None = None
    name: ScheduleNameField | None = None


class ScheduleCreateSchema(BaseModel):
    name: ScheduleNameField
    language: ZIMLangCode
    category: ScheduleCategory
    periodicity: SchedulePeriodicity
    tags: list[NotEmptyString] = Field(default_factory=list)
    enabled: bool
    config: dict[str, Any]  # will be validated in the route
    notification: ScheduleNotificationSchema | None = None
    context: NotEmptyString | None = None
    comment: str | None = None


class ScheduleCreateResponseSchema(BaseModel):
    id: UUID


class ScheduleUpdateSchema(BaseModel):
    name: ScheduleNameField | None = None
    language: ZIMLangCode | None = None
    category: ScheduleCategory | None = None
    periodicity: SchedulePeriodicity | None = None
    tags: list[NotEmptyString] | None = None
    enabled: bool | None = None
    offliner: Offliner | None = None
    warehouse_path: WarehousePathField | None = None
    image: DockerImageSchema | None = None
    platform: PlatformField | None = None
    resources: ResourcesSchema | None = None
    monitor: bool | None = None
    flags: dict[str, Any] | None = None
    artifacts_globs: list[NotEmptyString] | None = None
    context: str | None = None
    comment: str | None = None  # Optional comment for history tracking


class CloneSchema(BaseModel):
    name: ScheduleNameField
    comment: str | None = None
