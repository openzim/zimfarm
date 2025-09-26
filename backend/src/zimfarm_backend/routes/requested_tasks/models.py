from uuid import UUID

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    ZIMCPU,
    LimitFieldMax200,
    PriorityField,
    ScheduleNameField,
    SkipField,
    WorkerField,
    ZIMDisk,
    ZIMMemory,
)


# requested-tasks
class RequestedTaskSchema(BaseModel):
    skip: SkipField | None = None
    limit: LimitFieldMax200 | None = None

    worker: WorkerField | None = None
    priority: PriorityField | None = None
    schedule_name: list[ScheduleNameField] | None = None

    matching_cpu: ZIMCPU | None = None
    matching_memory: ZIMMemory | None = None
    matching_disk: ZIMDisk | None = None
    matching_offliners: list[str] | None = None


class NewRequestedTaskSchema(BaseModel):
    schedule_names: list[ScheduleNameField]
    priority: PriorityField | None = None
    worker: WorkerField | None = None


class NewRequestedTaskSchemaResponse(BaseModel):
    requested: list[UUID]


class UpdateRequestedTaskSchema(BaseModel):
    priority: PriorityField
