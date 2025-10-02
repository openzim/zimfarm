import datetime
from collections import defaultdict
from ipaddress import IPv4Address
from typing import Annotated, Any
from uuid import UUID

import pytz
from pydantic import AfterValidator, Field, computed_field

from zimfarm_backend.common import getnow
from zimfarm_backend.common.constants import WORKER_OFFLINE_DELAY_DURATION
from zimfarm_backend.common.enums import DockerImageName
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import ZIMCPU, ZIMDisk, ZIMMemory
from zimfarm_backend.common.schemas.models import (
    ExpandedScheduleConfigSchema,
    LanguageSchema,
    ScheduleConfigSchema,
    ScheduleNotificationSchema,
)
from zimfarm_backend.common.schemas.offliners.models import OfflinerSpecSchema


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

    cpu: ZIMCPU
    disk: ZIMDisk
    memory: ZIMMemory


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
    requested_by: str
    original_schedule_name: str
    context: str
    priority: int


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
    canceled_by: str | None
    container: dict[str, Any]
    priority: int
    notification: ScheduleNotificationSchema | None
    files: dict[str, Any]
    upload: dict[str, Any]
    offliner_definition_id: UUID = Field(exclude=True)
    offliner: str
    version: str


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
    offliner_definition_id: UUID = Field(exclude=True)
    offliner: str
    version: str


class MostRecentTaskSchema(BaseModel):
    """
    Schema for reading a most recent task model with some fields
    """

    id: UUID
    status: str
    updated_at: MadeAwareDateTime
    timestamp: list[tuple[str, datetime.datetime]]


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


class ScheduleHistorySchema(BaseModel):
    """
    Schema for reading a schedule history model
    """

    id: UUID
    author: str
    created_at: datetime.datetime
    comment: str | None
    name: str
    category: str
    enabled: bool
    language_code: str
    tags: list[str]
    periodicity: str
    context: str
    # entries are serialized as dict[str, Any] instead of ScheduleConfigSchema
    # because the entry is possibly outdated and would fail validation as the
    # offliner schema evolves
    config: dict[str, Any]


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
    offliner_definition_id: UUID = Field(exclude=True)
    offliner: str
    version: str

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
    offliners: list[str]
    cpu: ZIMCPU
    memory: ZIMMemory
    disk: ZIMDisk
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


class RunningTask(BaseModel):
    id: UUID
    updated_at: datetime.datetime
    config: ExpandedScheduleConfigSchema
    schedule_name: str | None
    status: str
    timestamp: list[tuple[str, datetime.datetime]]
    worker_name: str
    duration: ScheduleDurationSchema
    remaining: float
    eta: datetime.datetime


class WorkerMetricsSchema(WorkerLightSchema):
    """
    Schema for reading a worker model with full details and metrics
    """

    running_tasks: list[RunningTask]
    nb_tasks_total: int
    nb_tasks_completed: int
    nb_tasks_succeeded: int
    nb_tasks_failed: int

    @computed_field
    @property
    def current_usage(self) -> ConfigResourcesSchema:
        total_cpu = 0
        total_memory = 0
        total_disk = 0
        for task in self.running_tasks:
            total_cpu += task.config.resources.cpu
            total_memory += task.config.resources.memory
            total_disk += task.config.resources.disk
        return ConfigResourcesSchema(
            cpu=total_cpu,
            memory=total_memory,
            disk=total_disk,
        )


class OfflinerDefinitionSchema(BaseModel):
    """
    Schema for reading a offliner definition model
    """

    id: UUID = Field(exclude=True)
    offliner: str
    version: str
    created_at: datetime.datetime
    # schema overshadows Pydantic's schema method, so, use schema_ instead
    schema_: OfflinerSpecSchema = Field(serialization_alias="schema")


class OfflinerSchema(BaseModel):
    """
    Schema for reading a offliner model
    """

    id: str
    base_model: str
    docker_image_name: DockerImageName
    command_name: str
