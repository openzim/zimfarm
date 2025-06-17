from typing import Any

from pydantic import field_validator

from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    LimitFieldMax200,
    ScheduleNameField,
    SkipField,
    WorkerField,
)


class TasksSchema(BaseModel):
    skip: SkipField
    limit: LimitFieldMax200
    status: list[TaskStatus] | None = None
    schedule_name: ScheduleNameField


class TaskCreateSchema(BaseModel):
    worker_name: WorkerField


class TaskUpdateSchema(BaseModel):
    event: TaskStatus
    payload: dict[str, Any]

    @field_validator("event", mode="after")
    @classmethod
    def validate_event(cls, v: TaskStatus):
        if v not in TaskStatus.all_events():
            raise ValueError(f"Invalid event: {v}")
        return v
