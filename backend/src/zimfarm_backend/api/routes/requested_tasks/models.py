from typing import Self
from uuid import UUID

from pydantic import Field
from pydantic.functional_validators import model_validator

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
    schedule_name: list[NotEmptyString] | None = None

    matching_cpu: ZIMCPU | None = None
    matching_memory: ZIMMemory | None = None
    matching_disk: ZIMDisk | None = None
    matching_offliners: list[str] | None = None


class NewRequestedTaskSchema(BaseModel):
    recipe_names: list[RecipeNameField] = Field(default_factory=list)
    schedule_names: list[RecipeNameField] = Field(
        default_factory=list
    )  # Kept for compatibility purposes
    priority: PriorityField | None = None
    worker: WorkerField | None = None

    @model_validator(mode="after")
    def check_recipe_names(self) -> Self:
        if self.recipe_names and self.schedule_names:
            raise ValueError("Only one of schedule_names and recipe_names must be set")
        if not (self.recipe_names or self.schedule_names):
            raise ValueError("One of schedule_names and recipe_names must be set")

        if self.schedule_names:
            self.recipe_names = self.schedule_names

        return self


class NewRequestedTaskSchemaResponse(BaseModel):
    requested: list[UUID]


class UpdateRequestedTaskSchema(BaseModel):
    priority: PriorityField
