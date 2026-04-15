from uuid import UUID

from pydantic import Field

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    ZIMCPU,
    LimitFieldMax200,
    NotEmptyString,
    PriorityField,
    RecipeNameField,
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
    recipe_name: list[NotEmptyString] | None = None

    matching_cpu: ZIMCPU | None = None
    matching_memory: ZIMMemory | None = None
    matching_disk: ZIMDisk | None = None
    matching_offliners: list[str] | None = None


class NewRequestedTaskSchema(BaseModel):
    recipe_names: list[RecipeNameField] = Field(default_factory=list)
    priority: PriorityField | None = None
    worker: WorkerField | None = None


class NewRequestedTaskSchemaResponse(BaseModel):
    requested: list[UUID]


class UpdateRequestedTaskSchema(BaseModel):
    priority: PriorityField
