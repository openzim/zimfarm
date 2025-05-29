from typing import Any

from pydantic import EmailStr

from zimfarm_backend.common.enums import (
    Offliner,
    Platform,
    ScheduleCategory,
    SchedulePeriodicity,
    TaskStatus,
)
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    ZIMCPU,
    LimitFieldMax200,
    LimitFieldMax500,
    NotEmptyString,
    PriorityField,
    ScheduleNameField,
    SkipField,
    WorkerField,
    ZIMDisk,
    ZIMMemory,
)
from zimfarm_backend.common.schemas.models import (
    DockerImageSchema,
    EventNotificationSchema,
    LanguageSchema,
    PlatformsLimitSchema,  # pyright: ignore[reportUnknownVariableType]
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


# requested-tasks
class RequestedTaskSchema(BaseModel):
    skip: SkipField
    limit: LimitFieldMax200

    worker: WorkerField
    priority: PriorityField
    schedule_name: list[ScheduleNameField] | None = None

    matching_cpu: ZIMCPU | None = None
    matching_memory: ZIMMemory | None = None
    matching_disk: ZIMDisk | None = None
    matching_offliners: list[Offliner] | None = None


# requested-tasks for worker
class WorkerRequestedTaskSchema(BaseModel):
    worker: WorkerField
    avail_cpu: ZIMCPU
    avail_memory: ZIMMemory
    avail_disk: ZIMDisk


# requested-tasks POST
class NewRequestedTaskSchema(BaseModel):
    schedule_names: list[ScheduleNameField]
    priority: PriorityField
    worker: WorkerField


# requested-tasks PATCH
class UpdateRequestedTaskSchema(BaseModel):
    priority: PriorityField


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


# tasks GET
class TasksSchema(BaseModel):
    skip: SkipField
    limit: LimitFieldMax200
    status: list[TaskStatus] | None = None
    schedule_name: ScheduleNameField


# tasks POST
class TaskCreateSchema(BaseModel):
    worker_name: WorkerField


# tasks PATCH
class TasKUpdateSchema(BaseModel):
    event: EventNotificationSchema
    payload: dict[str, Any]


# users keys POST
class KeySchema(BaseModel):
    name: NotEmptyString
    key: NotEmptyString


# users POST
class UserCreateSchema(BaseModel):
    username: NotEmptyString
    password: NotEmptyString
    email: EmailStr
    role: RoleEnum


# users PATCH
class UserUpdateSchema(BaseModel):
    email: EmailStr
    role: RoleEnum | None = None


# workers checkin
class WorkerCheckInSchema(BaseModel):
    username: NotEmptyString
    selfish: bool | None = None
    cpu: ZIMCPU
    memory: ZIMMemory
    disk: ZIMDisk
    offliners: list[Offliner]
    platforms: PlatformsLimitSchema  # pyright: ignore[reportInvalidTypeForm]
