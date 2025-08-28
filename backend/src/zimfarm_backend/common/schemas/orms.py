import datetime
from collections import defaultdict
from ipaddress import IPv4Address
from typing import Annotated, Any
from uuid import UUID

import pytz
from pydantic import AfterValidator, Field, computed_field

from zimfarm_backend.common import getnow
from zimfarm_backend.common.constants import WORKER_OFFLINE_DELAY_DURATION
from zimfarm_backend.common.enums import Offliner
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.models import (
    ExpandedScheduleConfigSchema,
    LanguageSchema,
    ScheduleConfigSchema,
    ScheduleNotificationSchema,
)


def make_datetime_aware(dt: datetime.datetime) -> datetime.datetime:
    """Make the datetime localized so that it is serialized with a trailing 'Z'"""
    if dt.tzinfo is None:
        return pytz.utc.localize(dt)
    return dt


MadeAwareDateTime = Annotated[datetime.datetime, AfterValidator(make_datetime_aware)]


class ConfigResourcesSchema(BaseModel):
    """
    Schema for reading a config's resources
    """

    cpu: int
    disk: int
    memory: int


class ConfigWithOnlyResourcesSchema(BaseModel):
    """
    Schema for reading a config model with only its resources
    """

    resources: ConfigResourcesSchema


class ConfigWithOnlyOfflinerAndResourcesSchema(ConfigWithOnlyResourcesSchema):
    """
    Schema for reading a config model with only its offliner and resources
    """

    offliner: str


class BaseTaskSchema(BaseModel):
    """
    Schema for reading a task model with some fields
    """

    id: UUID
    status: str
    timestamp: list[tuple[str, datetime.datetime]]
    schedule_name: str | None
    worker_name: str
    updated_at: datetime.datetime
    original_schedule_name: str
    context: str


class TaskLightSchema(BaseTaskSchema):
    """
    Schema for reading a task model with some fields
    """

    config: ConfigWithOnlyResourcesSchema


class TaskFullSchema(BaseTaskSchema):
    """
    Schema for reading a task model with all fields
    """

    config: ExpandedScheduleConfigSchema
    events: list[dict[str, str | datetime.datetime]]
    debug: dict[str, Any]
    requested_by: str
    canceled_by: str | None
    container: dict[str, Any]
    priority: int
    notification: ScheduleNotificationSchema | None
    files: dict[str, Any]
    upload: dict[str, Any]


class ScheduleAwareTaskFullSchema(TaskFullSchema):
    """
    Schema for reading a task model with all fields and its schedule name
    """


class BaseRequestedTaskSchema(BaseModel):
    id: UUID
    status: str
    timestamp: list[tuple[str, datetime.datetime]]
    requested_by: str
    priority: int
    schedule_name: str | None
    original_schedule_name: str
    worker_name: str | None
    updated_at: datetime.datetime
    context: str


class RequestedTaskLightSchema(BaseRequestedTaskSchema):
    """
    Schema for reading a requested task model with some fields
    """

    config: ConfigWithOnlyOfflinerAndResourcesSchema


class RequestedTaskFullSchema(BaseRequestedTaskSchema):
    """
    Schema for reading a requested task model with all fields
    """

    config: ExpandedScheduleConfigSchema
    events: list[dict[str, str | datetime.datetime]]
    upload: dict[str, Any]
    notification: ScheduleNotificationSchema | None
    rank: int | None = None
    schedule_id: UUID | None = Field(exclude=True)
    context: str


class MostRecentTaskSchema(BaseModel):
    """
    Schema for reading a most recent task model with some fields
    """

    id: UUID
    status: str
    updated_at: MadeAwareDateTime


class ConfigOfflinerOnlySchema(BaseModel):
    """
    Schema for reading a config model with only its offliner
    """

    offliner: str


class ScheduleLightSchema(BaseModel):
    """
    Schema for reading a schedule model with some fields
    """

    name: str
    category: str
    most_recent_task: MostRecentTaskSchema | None
    config: ConfigOfflinerOnlySchema
    language: LanguageSchema
    enabled: bool
    nb_requested_tasks: int = Field(exclude=True)
    context: str

    @computed_field
    @property
    def is_requested(self) -> bool:
        return self.nb_requested_tasks > 0


class ScheduleDurationSchema(BaseModel):
    """
    Schema for reading a schedule duration model
    """

    value: int
    on: datetime.datetime
    worker_name: str | None
    default: bool


class ScheduleFullSchema(BaseModel):
    """
    Schema for reading a schedule model with all fields
    """

    language: LanguageSchema
    durations: list[ScheduleDurationSchema] = Field(exclude=True)
    name: str
    category: str
    config: ScheduleConfigSchema | ExpandedScheduleConfigSchema
    enabled: bool
    tags: list[str]
    periodicity: str
    notification: ScheduleNotificationSchema | None
    most_recent_task: MostRecentTaskSchema | None
    nb_requested_tasks: int = Field(exclude=True)
    is_valid: bool
    context: str

    @computed_field
    @property
    def is_requested(self) -> bool:
        return self.nb_requested_tasks > 0

    @computed_field
    @property
    def duration(self) -> dict[str, Any]:
        duration_res: dict[str, Any] = {}
        duration_res["available"] = False
        duration_res["default"] = None
        workers_duration: dict[str, dict[str, Any]] = defaultdict(dict)
        for duration in self.durations:
            if duration.default:
                duration_res["default"] = ScheduleDurationSchema.model_validate(
                    duration
                ).model_dump(mode="json")
            if duration.worker_name:
                duration_res["available"] = True
                workers_duration["workers"][duration.worker_name] = (
                    ScheduleDurationSchema.model_validate(duration).model_dump(
                        mode="json"
                    )
                )
        return {
            **duration_res,
            "workers": workers_duration["workers"] if workers_duration else None,
        }


class Worker(BaseModel):
    """
    Schema for reading a worker model
    """

    id: UUID
    name: str
    offliners: list[Offliner]
    cpu: int
    memory: int
    disk: int
    last_seen: datetime.datetime | None = None
    last_ip: IPv4Address | None = None
    deleted: bool
    user_id: UUID


class WorkerLightSchema(BaseModel):
    """
    Schema for reading a worker model with some fields
    """

    last_seen: datetime.datetime | None
    name: str
    last_ip: IPv4Address | None
    resources: ConfigResourcesSchema
    username: str
    offliners: list[str]
    contexts: list[str]

    @computed_field
    @property
    def status(self) -> str:
        if (
            self.last_seen
            and (getnow() - self.last_seen).total_seconds()
            < WORKER_OFFLINE_DELAY_DURATION
        ):
            return "online"
        return "offline"
