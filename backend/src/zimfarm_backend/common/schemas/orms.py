import datetime
from ipaddress import IPv4Address
from typing import Annotated, Any
from uuid import UUID

import pytz
from pydantic import AfterValidator, Field, computed_field

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
    timestamp: dict[str, Any]
    schedule_name: str
    worker_name: str = Field(serialization_alias="worker")
    updated_at: datetime.datetime
    original_schedule_name: str


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
    events: list[dict[str, Any]]
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

    schedule_name: str


class BaseRequestedTaskSchema(BaseModel):
    id: UUID
    status: str
    timestamp: dict[str, Any]
    requested_by: str
    priority: int
    schedule_name: str
    original_schedule_name: str
    worker_name: str
    updated_at: datetime.datetime


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
    events: list[dict[str, Any]]
    upload: dict[str, Any]
    notification: ScheduleNotificationSchema | None
    rank: int | None = None
    schedule_name: str
    schedule_id: UUID | None = Field(exclude=True)


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

    language_code: str = Field(exclude=True)
    language_name_en: str = Field(exclude=True)
    language_name_native: str = Field(exclude=True)
    durations: list[ScheduleDurationSchema]
    name: str
    category: str
    config: ScheduleConfigSchema | ExpandedScheduleConfigSchema
    enabled: bool
    tags: list[str]
    periodicity: str
    notification: ScheduleNotificationSchema | None
    most_recent_task: MostRecentTaskSchema | None
    nb_requested_tasks: int = Field(exclude=True)

    @computed_field
    @property
    def is_requested(self) -> bool:
        return self.nb_requested_tasks > 0

    @computed_field
    @property
    def language(self) -> LanguageSchema:
        return LanguageSchema(
            code=self.language_code,
            name_en=self.language_name_en,
            name_native=self.language_name_native,
        )

    @computed_field
    @property
    def duration(self) -> dict[str, Any]:
        duration_res: dict[str, Any] = {}
        duration_res["available"] = False
        duration_res["default"] = {}
        duration_res["workers"] = {}
        for duration in self.durations:
            if duration.default:
                duration_res["default"] = ScheduleDurationSchema.model_validate(
                    duration
                ).model_dump(mode="json")
            if duration.worker_name:
                duration_res["available"] = True
                duration_res["workers"][duration.worker_name] = (
                    ScheduleDurationSchema.model_validate(duration).model_dump(
                        mode="json"
                    )
                )
        return duration_res


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

    last_seen: datetime.datetime
    name: str
    last_ip: IPv4Address | None
    resources: ConfigResourcesSchema
    username: str
    offliners: list[str]

    @computed_field
    @property
    def status(self) -> str:
        if (
            datetime.datetime.now(datetime.UTC).replace(tzinfo=None) - self.last_seen
        ).total_seconds() < WORKER_OFFLINE_DELAY_DURATION:
            return "online"
        return "offline"
