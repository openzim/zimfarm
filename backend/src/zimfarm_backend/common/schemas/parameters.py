from typing import Any

from zimfarm_backend.common.enums import (
    Offliner,
    Platform,
    ScheduleCategory,
    SchedulePeriodicity,
)
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    ZIMCPU,
    LimitFieldMax200,
    LimitFieldMax500,
    NotEmptyString,
    ScheduleNameField,
    SkipField,
    WorkerField,
    ZIMDisk,
    ZIMMemory,
)
from zimfarm_backend.common.schemas.models import (
    DockerImageSchema,
    LanguageSchema,
    ResourcesSchema,
    WarehousePath,
)


# languages GET
class SkipLimit500Schema(BaseModel):
    skip: SkipField
    limit: LimitFieldMax500


# tags GET, # users GET, # workers GET
class SkipLimitSchema(BaseModel):
    skip: SkipField
    limit: LimitFieldMax200


# requested-tasks for worker
class WorkerRequestedTaskSchema(BaseModel):
    worker: WorkerField
    avail_cpu: ZIMCPU
    avail_memory: ZIMMemory
    avail_disk: ZIMDisk


# schedule GET
class SchedulesSchema(BaseModel):
    skip: SkipField
    limit: LimitFieldMax200
    category: list[ScheduleCategory] | None = None
    tag: list[NotEmptyString]
    lang: list[NotEmptyString] | None = None
    name: ScheduleNameField


# schedule PATCH
class UpdateSchema(BaseModel):
    name: ScheduleNameField
    language: LanguageSchema
    category: ScheduleCategory
    periodicity: SchedulePeriodicity
    tags: list[NotEmptyString]
    enabled: bool = False
    task_name: Offliner
    warehouse_path: WarehousePath | None = None
    image: DockerImageSchema | None = None
    platform: Platform | None = None
    resources: ResourcesSchema | None = None
    monitor: bool = False
    flags: dict[str, Any] | None = None
    artifacts_globs: list[NotEmptyString] | None = None


# schedule clone
class CloneSchema(BaseModel):
    name: ScheduleNameField
